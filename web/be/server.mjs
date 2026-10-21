import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";
import { createReadStream, createWriteStream } from "node:fs";
import { readFile, stat, mkdir, rm } from "node:fs/promises";
import { Transform } from "node:stream";
import { pipeline } from "node:stream/promises";
import { z } from "zod";
import { Store } from "./store.mjs";
import { loadConfig } from "./config.mjs";
import {
  digest,
  sessionFor,
  sessionCookie,
  requireMutation,
  CognitoAuth,
} from "./auth.mjs";
import { Analyzer, startWorker } from "./analysis.mjs";

const projectInput = z
  .object({
    app: z.string().trim().min(1).max(100),
    goal: z.string().trim().min(1).max(1000),
  })
  .strict();
const idPattern = "[a-f0-9-]{36}";
const fail = (status, message) => Object.assign(new Error(message), { status });
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".txt": "text/plain",
};

async function jsonBody(req) {
  if (!String(req.headers["content-type"] || "").startsWith("application/json"))
    throw fail(415, "Send application/json.");
  let bytes = 0,
    chunks = [];
  for await (const chunk of req) {
    bytes += chunk.length;
    if (bytes > 16384) throw fail(413, "Request is too large.");
    chunks.push(chunk);
  }
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw fail(400, "Request body must be valid JSON.");
  }
}

export async function createService({
  config = loadConfig(),
  analyzer,
  auth,
  workerEnabled = true,
} = {}) {
  if (config.profile) process.env.AWS_PROFILE ||= config.profile;
  const store = new Store(config.dataDir);
  const uploads = path.join(config.dataDir, "uploads");
  await mkdir(uploads, { recursive: true, mode: 0o700 });
  // Interrupted streams are never treated as usable input after a restart.
  for (const file of store.all("SELECT * FROM files WHERE ready=0")) {
    await rm(file.path, { force: true });
    store.run("DELETE FROM files WHERE id=?", file.id);
  }
  store.run("DELETE FROM sessions WHERE expires<?", Date.now());
  analyzer ||= new Analyzer(config);
  auth ||= new CognitoAuth(config);
  let readiness = await analyzer.readiness();
  const worker = workerEnabled ? startWorker(store, analyzer, config) : null;

  function limited(key, max, interval) {
    const now = Date.now();
    if (
      store.get(
        "SELECT count(*) AS n FROM attempts WHERE key=? AND at>?",
        key,
        now - interval,
      ).n >= max
    )
      throw fail(429, "Too many attempts. Please try again later.");
    store.run("INSERT INTO attempts(key,at) VALUES(?,?)", key, now);
    store.run("DELETE FROM attempts WHERE at<?", now - 86400000);
  }
  function send(res, status, body, extra = {}) {
    res.writeHead(status, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extra,
    });
    res.end(JSON.stringify(body));
  }
  const server = http.createServer(async (req, res) => {
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("Referrer-Policy", "no-referrer");
    res.setHeader(
      "Permissions-Policy",
      "camera=(), microphone=(), geolocation=()",
    );
    res.setHeader("Cross-Origin-Resource-Policy", "same-origin");
    res.setHeader("X-Frame-Options", "DENY");
    res.setHeader(
      "Content-Security-Policy",
      "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'",
    );
    if (config.secure)
      res.setHeader("Strict-Transport-Security", "max-age=31536000");
    try {
      const url = new URL(req.url || "/", config.origin);
      const route = url.pathname;
      const method = req.method || "GET";
      const session = sessionFor(req, store);
      if (route === "/auth/login" && method === "GET") {
        limited(
          `signin:${digest(req.socket.remoteAddress || "unknown")}`,
          30,
          900000,
        );
        const login = auth.begin(store);
        res.writeHead(302, {
          Location: login.url,
          "Set-Cookie": login.cookie,
          "Cache-Control": "no-store",
        });
        res.end();
        return;
      }
      if (route === "/auth/callback" && method === "GET") {
        const result = await auth.callback(url, req, store);
        res.writeHead(302, {
          Location: config.origin + "/",
          "Cache-Control": "no-store",
          "Set-Cookie": [
            sessionCookie(
              result.session.token,
              config,
              false,
              result.session.maxAge,
            ),
            `rea_oauth=; Path=/auth; HttpOnly; SameSite=Lax; Max-Age=0${config.secure ? "; Secure" : ""}`,
          ],
        });
        res.end();
        return;
      }
      if (route.startsWith("/api/")) {
        if (["POST", "PUT", "PATCH", "DELETE"].includes(method))
          requireMutation(req, session, config);
        if (method === "GET" && route === "/api/config")
          return send(res, 200, {
            mode: "live",
            auth: { provider: "cognito", configured: auth.configured },
            analysis: {
              modelConfigured: Boolean(config.modelId),
              executorReady: readiness.ready,
              reason: readiness.ready
                ? config.modelId
                  ? ""
                  : "Configure an accessible Bedrock model before running assessments."
                : readiness.reason,
            },
            limits: {
              maxFileBytes: config.maxFileBytes,
              maxProjectBytes: config.maxProjectBytes,
              maxFiles: config.maxFiles,
              analyzedFilesPerAssessment: 3,
            },
            paymentsEnabled: false,
          });
        if (method === "GET" && route === "/api/session")
          return send(res, 200, {
            user: session
              ? {
                  id: session.user_id,
                  name: session.name,
                  email: session.email,
                }
              : null,
            csrf: session?.csrf || null,
          });
        if (!session)
          throw fail(401, "Sign in to access your private workspace.");
        const userId = session.user_id;
        if (route === "/api/auth/logout" && method === "POST") {
          store.run("DELETE FROM sessions WHERE token=?", session.token);
          return send(
            res,
            200,
            { ok: true, logoutUrl: auth.logoutUrl() },
            { "Set-Cookie": sessionCookie("", config, true) },
          );
        }
        if (route === "/api/projects" && method === "GET")
          return send(res, 200, {
            projects: store
              .all(
                "SELECT * FROM projects WHERE user_id=? ORDER BY created DESC",
                userId,
              )
              .map((p) => store.detail(p)),
          });
        if (route === "/api/projects" && method === "POST") {
          const input = projectInput.parse(await jsonBody(req));
          const key = req.headers["x-idempotency-key"] || null;
          if (key && (typeof key !== "string" || !/^[a-f0-9-]{36}$/.test(key)))
            throw fail(400, "Invalid project request identifier.");
          const row = store.transaction(() => {
            if (key) {
              const prior = store.get(
                "SELECT * FROM projects WHERE user_id=? AND create_key=?",
                userId,
                key,
              );
              if (prior) {
                if (prior.app !== input.app || prior.goal !== input.goal)
                  throw fail(
                    409,
                    "This project request was already used for a different goal.",
                  );
                return prior;
              }
            }
            if (
              store.get(
                "SELECT count(*) AS n FROM projects WHERE user_id=?",
                userId,
              ).n >= 20
            )
              throw fail(
                429,
                "This workspace has reached its saved-project limit.",
              );
            const id = randomUUID();
            store.run(
              "INSERT INTO projects(id,user_id,app,goal,created,create_key) VALUES(?,?,?,?,?,?)",
              id,
              userId,
              input.app,
              input.goal,
              Date.now(),
              key,
            );
            return store.owner(userId, id);
          });
          return send(res, 201, { project: store.detail(row) });
        }
        const match = route.match(
          new RegExp(
            `^/api/projects/(${idPattern})(?:/(assessment|files|report|goal|link)(?:/(${idPattern}))?)?$`,
          ),
        );
        if (!match) throw fail(404, "Endpoint not found.");
        const [, projectId, resource, fileId] = match;
        const project = store.owner(userId, projectId);
        if (!project) throw fail(404, "Project not found.");
        if (!resource && method === "GET")
          return send(res, 200, {
            project: store.detail(
              project,
              url.searchParams.get("evidence") === "1",
            ),
          });
        if (!resource && method === "DELETE") {
          const files = store.all(
            "SELECT path FROM files WHERE project_id=?",
            projectId,
          );
          store.run(
            "UPDATE jobs SET status='cancelled',activity='Project deleted' WHERE project_id=? AND status IN ('running','queued')",
            projectId,
          );
          // In-flight workers observe cancellation before they can publish results.
          store.run("DELETE FROM projects WHERE id=?", projectId);
          for (const file of files) await rm(file.path, { force: true });
          return send(res, 200, { ok: true });
        }
        if (resource === "report" && method === "GET")
          return send(res, 200, {
            project: { id: project.id, app: project.app, goal: project.goal },
            assessment: project.assessment
              ? JSON.parse(project.assessment)
              : null,
            evidence: store.detail(project, true).evidence,
          });
        if (resource === "goal" && method === "PATCH") {
          const input = z
            .object({ goal: z.string().trim().min(1).max(1000) })
            .strict()
            .parse(await jsonBody(req));
          store.transaction(() => {
            store.run(
              "UPDATE jobs SET status='cancelled',activity='Goal changed',updated=? WHERE project_id=? AND status IN ('running','queued')",
              Date.now(),
              projectId,
            );
            store.run(
              "UPDATE projects SET goal=?,revision=revision+1,status='needs_input',activity='Goal updated. Previous findings remain available.' WHERE id=?",
              input.goal,
              projectId,
            );
          });
          return send(res, 200, {
            project: store.detail(store.owner(userId, projectId)),
          });
        }
        if (resource === "link" && method === "PUT") {
          const { link } = z
            .object({ link: z.string().max(2000) })
            .strict()
            .parse(await jsonBody(req));
          if (link && !/^https?:\/\//i.test(link))
            throw fail(400, "Use an http or https reference link.");
          store.run("UPDATE projects SET link=? WHERE id=?", link, projectId);
          return send(res, 200, {
            project: store.detail(store.owner(userId, projectId)),
          });
        }
        if (resource === "assessment" && method === "POST") {
          if (!config.modelId)
            throw fail(
              503,
              "The assessment service is not ready yet. Your project and files are saved.",
            );
          readiness = await analyzer.readiness();
          if (!readiness.ready)
            throw fail(
              503,
              "The analysis service is currently unavailable. Your project and files are saved.",
            );
          const id = store.queue(userId, projectId);
          return send(res, 202, {
            jobId: id,
            project: store.detail(store.owner(userId, projectId)),
          });
        }
        if (resource === "assessment" && method === "DELETE") {
          store.run(
            "UPDATE jobs SET status='cancelled',activity='Cancelled by owner',updated=? WHERE project_id=? AND status IN ('queued','running')",
            Date.now(),
            projectId,
          );
          store.run(
            "UPDATE projects SET status='cancelled',activity='Assessment cancelled. Saved evidence is preserved.' WHERE id=?",
            projectId,
          );
          return send(res, 200, {
            project: store.detail(store.owner(userId, projectId)),
          });
        }
        if (resource === "files" && !fileId && method === "POST") {
          if (["queued", "running"].includes(project.status))
            throw fail(
              409,
              "Cancel the active assessment before changing its source material.",
            );
          let name;
          try {
            name = decodeURIComponent(String(req.headers["x-file-name"] || ""));
          } catch {
            throw fail(400, "Invalid file name.");
          }
          if (!name || name.length > 240 || /[\x00-\x1f\x7f]/.test(name))
            throw fail(400, "A valid file name is required.");
          const expected = Number(req.headers["content-length"]);
          if (
            !Number.isSafeInteger(expected) ||
            expected < 1 ||
            expected > config.maxFileBytes
          )
            throw fail(
              413,
              `Source files must be 1–${Math.floor(config.maxFileBytes / 1048576)} MiB.`,
            );
          const file = {
            id: randomUUID(),
            path: path.join(uploads, randomUUID()),
            name: path.basename(name),
            bytes: expected,
          };
          store.transaction(() => {
            if (
              store.get(
                "SELECT id FROM jobs WHERE project_id=? AND status IN ('queued','running')",
                projectId,
              )
            )
              throw fail(
                409,
                "Cancel the active assessment before adding files.",
              );
            const existing = store.get(
              "SELECT count(*) AS n,coalesce(sum(bytes),0) AS bytes FROM files WHERE project_id=?",
              projectId,
            );
            if (
              existing.n >= config.maxFiles ||
              existing.bytes + expected > config.maxProjectBytes
            )
              throw fail(
                413,
                "This project has reached its source-material limit.",
              );
            store.run(
              "INSERT INTO files(id,project_id,name,bytes,path,created) VALUES(?,?,?,?,?,?)",
              file.id,
              projectId,
              file.name,
              expected,
              file.path,
              Date.now(),
            );
          });
          let received = 0;
          const hash = createHash("sha256");
          const meter = new Transform({
            transform(chunk, _encoding, callback) {
              received += chunk.length;
              if (received > expected)
                callback(fail(413, "Upload exceeds its declared size."));
              else {
                hash.update(chunk);
                callback(null, chunk);
              }
            },
          });
          try {
            await pipeline(
              req,
              meter,
              createWriteStream(file.path, { flags: "wx", mode: 0o600 }),
            );
            if (received !== expected)
              throw fail(400, "The upload was incomplete.");
            if (!store.owner(userId, projectId))
              throw fail(404, "Project was deleted during upload.");
            store.run(
              "UPDATE files SET ready=1,sha256=? WHERE id=?",
              hash.digest("hex"),
              file.id,
            );
            return send(res, 201, {
              project: store.detail(store.owner(userId, projectId)),
            });
          } catch (error) {
            await rm(file.path, { force: true });
            store.run("DELETE FROM files WHERE id=?", file.id);
            throw error;
          }
        }
        if (resource === "files" && fileId && method === "DELETE") {
          if (["queued", "running"].includes(project.status))
            throw fail(
              409,
              "Cancel the active assessment before deleting source material.",
            );
          const file = store.file(userId, projectId, fileId);
          if (!file) throw fail(404, "File not found.");
          await rm(file.path, { force: true });
          store.run("DELETE FROM files WHERE id=?", fileId);
          return send(res, 200, {
            project: store.detail(store.owner(userId, projectId)),
          });
        }
        throw fail(405, "Method not allowed.");
      }
      if (!["GET", "HEAD"].includes(method))
        throw fail(405, "Method not allowed.");
      const decoded = decodeURIComponent(route);
      if (decoded.includes("\0") || decoded.includes("\\"))
        throw fail(404, "Page not found.");
      const requested = path.resolve(
        config.staticDir,
        `.${decoded === "/" ? "/index.html" : decoded}`,
      );
      if (
        requested !== config.staticDir &&
        !requested.startsWith(config.staticDir + path.sep)
      )
        throw fail(404, "Page not found.");
      let info;
      try {
        info = await stat(requested);
      } catch {
        throw fail(404, "Page not found.");
      }
      if (!info.isFile()) throw fail(404, "Page not found.");
      res.setHeader(
        "Content-Type",
        types[path.extname(requested)] || "application/octet-stream",
      );
      res.setHeader(
        "Cache-Control",
        requested.endsWith(".html") ? "no-store" : "public, max-age=3600",
      );
      if (requested === path.join(config.staticDir, "index.html")) {
        const html = (await readFile(requested, "utf8")).replace(
          "</head>",
          '<meta name="rea-mode" content="live"></head>',
        );
        res.end(method === "HEAD" ? undefined : html);
      } else if (method === "HEAD") res.end();
      else await pipeline(createReadStream(requested), res);
    } catch (error) {
      if (res.headersSent || res.destroyed) {
        res.destroy();
        return;
      }
      if (error instanceof z.ZodError)
        return send(res, 400, {
          error: "Some fields are missing or invalid.",
          fields: error.issues.map((i) => ({
            field: i.path.join("."),
            message: i.message,
          })),
        });
      const status = error.status || 500;
      send(res, status, {
        error:
          status < 500 || error.status
            ? error.message
            : "The service could not complete this request.",
      });
    }
  });
  server.requestTimeout = 600000;
  server.headersTimeout = 30000;
  return {
    server,
    store,
    worker,
    config,
    async close() {
      await worker?.stop();
      await new Promise((resolve) => server.close(resolve));
      store.close();
    },
  };
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const service = await createService();
  service.server.listen(service.config.port, service.config.host, () =>
    console.log(
      `REA workspace: ${service.config.origin} · AWS credentials: ${service.config.profile || "runtime IAM role"}`,
    ),
  );
  for (const signal of ["SIGINT", "SIGTERM"])
    process.once(signal, async () => {
      await service.close();
      process.exit(0);
    });
}
