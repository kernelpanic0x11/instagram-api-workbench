import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm, readFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createService } from "../server.mjs";
import { loadConfig } from "../config.mjs";
import { newSession } from "../auth.mjs";
import { validateAssessment, startWorker } from "../analysis.mjs";

function assessment(evidence) {
  return {
    summary: "Test-only report from injected provider fixtures.",
    findings: [
      {
        title: "Artifact inventory",
        body: "The injected fixture reported an inventory.",
        evidenceIds: [evidence[0].id],
        confidence: "observed",
      },
    ],
    limitations: [
      "Test provider fixtures do not establish real REA or Bedrock behavior.",
    ],
    nextScope: {
      title: "Trace the requested behavior",
      deliverables: ["Evidence-backed report"],
      exclusions: ["Server behavior"],
      completionCriteria: ["Cite reproducible observations"],
    },
  };
}
const fakeAnalyzer = {
  readiness: async () => ({ ready: true }),
  inspect: async () => ({
    fixture: true,
    format: "text",
    coverage: "inventory",
  }),
  summarize: async (_project, evidence) => assessment(evidence),
};

test("retries after sign-in create one project per owner and request key", async () =>
  fixture(async ({ request, bob }) => {
    const headers = {
      "x-idempotency-key": "11111111-1111-4111-8111-111111111111",
    };
    const body = { app: "Example", goal: "An idempotent investigation" };
    const first = await request("/api/projects", {
      method: "POST",
      body,
      headers,
    });
    const retry = await request("/api/projects", {
      method: "POST",
      body,
      headers,
    });
    assert.equal(first.status, 201);
    assert.equal(retry.body.project.id, first.body.project.id);
    assert.equal((await request("/api/projects")).body.projects.length, 1);
    assert.equal(
      (
        await request("/api/projects", {
          method: "POST",
          body: { ...body, goal: "A different goal" },
          headers,
        })
      ).status,
      409,
    );
    const otherOwner = await request("/api/projects", {
      who: bob,
      method: "POST",
      body,
      headers,
    });
    assert.equal(otherOwner.status, 201);
    assert.notEqual(otherOwner.body.project.id, first.body.project.id);
  }));

async function fixture(fn, analyzer = fakeAnalyzer) {
  const dir = await mkdtemp(path.join(os.tmpdir(), "rea-service-"));
  const config = loadConfig({
    DATA_DIR: dir,
    BEDROCK_MODEL_ID: "test-only-injected-provider",
    FRONTEND_DIST: "../fe/dist",
    MAX_FILE_BYTES: "1024",
  });
  const service = await createService({
    config,
    analyzer,
    workerEnabled: false,
  });
  await new Promise((resolve) =>
    service.server.listen(0, "127.0.0.1", resolve),
  );
  config.origin = `http://127.0.0.1:${service.server.address().port}`;
  function identity(id) {
    service.store.run(
      "INSERT INTO users(id,email,name,subject,created) VALUES(?,?,?,?,?)",
      id,
      `${id}@example.com`,
      id,
      `test|${id}`,
      Date.now(),
    );
    return newSession({ id }, service.store, config);
  }
  const alice = identity("alice"),
    bob = identity("bob");
  async function request(
    route,
    {
      who = alice,
      method = "GET",
      body,
      headers = {},
      csrf = true,
      origin = config.origin,
    } = {},
  ) {
    const h = {
      ...(who ? { cookie: `rea_session=${who.token}` } : {}),
      ...(origin ? { origin } : {}),
      ...(who && csrf ? { "x-csrf-token": who.csrf } : {}),
      ...headers,
    };
    if (body && !(body instanceof Uint8Array)) {
      h["content-type"] = "application/json";
      body = JSON.stringify(body);
    }
    const response = await fetch(config.origin + route, {
      method,
      headers: h,
      body,
    });
    return {
      status: response.status,
      headers: response.headers,
      body: await response.json(),
    };
  }
  try {
    await fn({ ...service, request, alice, bob, config });
  } finally {
    await service.close();
    await rm(dir, { recursive: true, force: true });
  }
}

test("authenticated persistence, owner isolation, CSRF, and session revocation", async () =>
  fixture(async ({ request, store, alice }) => {
    assert.equal((await request("/api/projects", { who: null })).status, 401);
    assert.equal(
      (
        await request("/api/projects", {
          method: "POST",
          body: { app: "Example", goal: "Document one behavior" },
          csrf: false,
        })
      ).status,
      403,
    );
    assert.equal(
      (
        await request("/api/projects", {
          method: "POST",
          body: { app: "Example", goal: "Document one behavior" },
          origin: "https://attacker.example.com",
        })
      ).status,
      403,
    );
    const created = await request("/api/projects", {
      method: "POST",
      body: { app: "Example", goal: "Document one behavior" },
    });
    assert.equal(created.status, 201);
    const id = created.body.project.id;
    assert.equal(
      (await request("/api/projects/" + id)).body.project.app,
      "Example",
    );
    const bob = { ...alice, token: "x".repeat(43) };
    assert.equal(
      (await request("/api/projects/" + id, { who: bob })).status,
      401,
    );
    assert.equal(store.get("SELECT count(*) AS n FROM projects").n, 1);
    assert.equal(
      (await request("/api/auth/logout", { method: "POST", body: {} })).status,
      200,
    );
    assert.equal((await request("/api/projects")).status, 401);
  }));

test("another signed-in owner cannot read, upload to, export, change, or delete a private project", async () =>
  fixture(async ({ request, bob }) => {
    const id = (
      await request("/api/projects", {
        method: "POST",
        body: { app: "Private", goal: "Owner A only" },
      })
    ).body.project.id;
    for (const [suffix, method, body] of [
      ["", "GET"],
      ["/report", "GET"],
      ["/goal", "PATCH", { goal: "steal" }],
      ["", "DELETE"],
      ["/assessment", "POST", {}],
    ]) {
      assert.equal(
        (
          await request("/api/projects/" + id + suffix, {
            who: bob,
            method,
            body,
          })
        ).status,
        404,
      );
    }
    const bytes = new TextEncoder().encode("private source");
    assert.equal(
      (
        await request(`/api/projects/${id}/files`, {
          who: bob,
          method: "POST",
          body: bytes,
          headers: {
            "content-type": "application/octet-stream",
            "x-file-name": "secret.txt",
          },
        })
      ).status,
      404,
    );
  }));

test("bounded source uploads produce real digests, retain evidence after source deletion, and remove project data", async () =>
  fixture(async ({ request, store, config }) => {
    const id = (
      await request("/api/projects", {
        method: "POST",
        body: { app: "Inventory fixture", goal: "Inspect file structure" },
      })
    ).body.project.id;
    assert.equal(
      (
        await request(`/api/projects/${id}/assessment`, {
          method: "POST",
          body: {},
        })
      ).status,
      409,
    );
    const bytes = new TextEncoder().encode(
      "This is a synthetic test artifact.",
    );
    const upload = await request(`/api/projects/${id}/files`, {
      method: "POST",
      body: bytes,
      headers: {
        "content-type": "application/octet-stream",
        "x-file-name": encodeURIComponent("<example>.txt"),
      },
    });
    assert.equal(upload.status, 201);
    const file = upload.body.project.files[0];
    assert.match(file.sha256, /^[a-f0-9]{64}$/);
    assert.equal(file.bytes, bytes.length);
    const stored = store.get("SELECT * FROM files WHERE id=?", file.id);
    assert.deepEqual(await readFile(stored.path), Buffer.from(bytes));
    const tooLarge = await request(`/api/projects/${id}/files`, {
      method: "POST",
      body: new Uint8Array(1025),
      headers: {
        "content-type": "application/octet-stream",
        "x-file-name": "big.bin",
      },
    });
    assert.equal(tooLarge.status, 413);
    assert.equal(
      (
        await request(`/api/projects/${id}/assessment`, {
          method: "POST",
          body: {},
        })
      ).status,
      202,
    );
    const worker = startWorker(store, fakeAnalyzer, config);
    await worker.idle();
    await worker.stop();
    const result = (await request(`/api/projects/${id}`)).body.project;
    assert.equal(result.status, "ready");
    assert.equal(result.evidence.length, 1);
    assert.equal(
      result.assessment.findings[0].evidenceIds[0],
      result.evidence[0].id,
    );
    assert.equal(result.assessment.coverage.staticOnly, true);
    assert.equal(
      (
        await request(`/api/projects/${id}/files/${file.id}`, {
          method: "DELETE",
        })
      ).status,
      200,
    );
    const retained = (await request(`/api/projects/${id}/report`)).body;
    assert.equal(retained.evidence.length, 1);
    assert.equal(
      (await request(`/api/projects/${id}`, { method: "DELETE" })).status,
      200,
    );
    assert.equal(store.get("SELECT count(*) AS n FROM evidence").n, 0);
    assert.equal(store.get("SELECT count(*) AS n FROM jobs").n, 0);
  }));

test("evidence citations and required unknowns fail closed", () => {
  const evidence = [{ id: "known-evidence" }];
  assert.equal(
    validateAssessment(assessment(evidence), evidence).findings.length,
    1,
  );
  const invented = assessment([{ id: "invented" }]);
  assert.throws(() => validateAssessment(invented, evidence), /does not exist/);
  const noLimits = assessment(evidence);
  noLimits.limitations = [];
  assert.throws(() => validateAssessment(noLimits, evidence));
});

test("changed goals cancel active work and cannot receive stale results", async () => {
  let started;
  const began = new Promise((resolve) => {
    started = resolve;
  });
  const analyzer = {
    ...fakeAnalyzer,
    inspect: async (_file, signal) => {
      started();
      return new Promise((_resolve, reject) =>
        signal.addEventListener("abort", () => reject(signal.reason), {
          once: true,
        }),
      );
    },
  };
  await fixture(async ({ request, store, config }) => {
    const id = (
      await request("/api/projects", {
        method: "POST",
        body: { app: "Changing target", goal: "First goal" },
      })
    ).body.project.id;
    await request(`/api/projects/${id}/files`, {
      method: "POST",
      body: new TextEncoder().encode("fixture"),
      headers: { "x-file-name": "fixture.txt" },
    });
    await request(`/api/projects/${id}/assessment`, {
      method: "POST",
      body: {},
    });
    const worker = startWorker(store, analyzer, config);
    await began;
    assert.equal(
      (
        await request(`/api/projects/${id}/goal`, {
          method: "PATCH",
          body: { goal: "A different goal" },
        })
      ).status,
      200,
    );
    await worker.stop();
    const p = (await request(`/api/projects/${id}`)).body.project;
    assert.equal(p.goal, "A different goal");
    assert.equal(p.assessment, null);
    assert.equal(p.status, "needs_input");
    assert.equal(
      store.get("SELECT status FROM jobs WHERE project_id=?", id).status,
      "cancelled",
    );
  }, analyzer);
});
