import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { Store } from "../store.mjs";

test("queued jobs persist across database reopen and interrupted leases restore bounded work", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "rea-queue-"));
  let store = new Store(dir);
  try {
    store.run(
      "INSERT INTO users(id,email,name,subject,created) VALUES(?,?,?,?,?)",
      "alice",
      "alice@example.com",
      "Alice",
      "test|alice",
      Date.now(),
    );
    store.run(
      "INSERT INTO projects(id,user_id,app,goal,created) VALUES(?,?,?,?,?)",
      "project-a",
      "alice",
      "Example",
      "Understand one behavior",
      Date.now(),
    );
    store.run(
      "INSERT INTO files(id,project_id,name,bytes,path,ready,created) VALUES(?,?,?,?,?,1,?)",
      "file-a",
      "project-a",
      "fixture.bin",
      1,
      "/test-only/not-read",
      Date.now(),
    );
    const id = store.queue("alice", "project-a");
    assert.throws(() => store.queue("alice", "project-a"), /already active/);
    store.close();
    store = new Store(dir);
    assert.equal(
      store.get("SELECT status FROM jobs WHERE id=?", id).status,
      "queued",
    );
    const first = store.claim(1000);
    assert.equal(first.id, id);
    assert.equal(first.attempts, 1);
    store.run("UPDATE jobs SET lease_until=? WHERE id=?", Date.now() - 1, id);
    const second = store.claim(1000);
    assert.equal(second.id, id);
    assert.equal(second.attempts, 2);
    store.run("UPDATE jobs SET lease_until=? WHERE id=?", Date.now() - 1, id);
    assert.equal(store.claim(1000), null);
    assert.equal(
      store.get("SELECT status FROM jobs WHERE id=?", id).status,
      "failed",
    );
    assert.equal(
      store.get("SELECT status FROM projects WHERE id=?", "project-a").status,
      "failed",
    );
  } finally {
    store.close();
    await rm(dir, { recursive: true, force: true });
  }
});

test("an in-flight upload blocks queue admission, and owner checks apply before job creation", async () => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "rea-admission-"));
  const store = new Store(dir);
  try {
    store.run(
      "INSERT INTO users(id,email,name,subject,created) VALUES(?,?,?,?,?)",
      "alice",
      "alice@example.com",
      "Alice",
      "test|alice",
      Date.now(),
    );
    store.run(
      "INSERT INTO projects(id,user_id,app,goal,created) VALUES(?,?,?,?,?)",
      "project-a",
      "alice",
      "Example",
      "Inspect",
      Date.now(),
    );
    store.run(
      "INSERT INTO files(id,project_id,name,bytes,path,ready,created) VALUES(?,?,?,?,?,0,?)",
      "file-a",
      "project-a",
      "fixture.bin",
      1,
      "/test-only/not-read",
      Date.now(),
    );
    assert.throws(() => store.queue("alice", "project-a"), /uploads to finish/);
    assert.throws(() => store.queue("bob", "project-a"), /not found/);
    assert.equal(store.get("SELECT count(*) AS n FROM jobs").n, 0);
  } finally {
    store.close();
    await rm(dir, { recursive: true, force: true });
  }
});
