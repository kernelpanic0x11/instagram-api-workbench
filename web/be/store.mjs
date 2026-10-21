import { DatabaseSync } from "node:sqlite";
import { mkdirSync, chmodSync } from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";

export class Store {
  constructor(dir) {
    mkdirSync(dir, { recursive: true, mode: 0o700 });
    this.db = new DatabaseSync(path.join(dir, "workspace.sqlite"));
    chmodSync(path.join(dir, "workspace.sqlite"), 0o600);
    this.db
      .exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;
      CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,subject TEXT UNIQUE NOT NULL,created INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS oauth_states(state TEXT PRIMARY KEY,binding TEXT NOT NULL,verifier TEXT NOT NULL,nonce TEXT NOT NULL,expires INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,csrf TEXT NOT NULL,expires INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),app TEXT NOT NULL,goal TEXT NOT NULL,created INTEGER NOT NULL,revision INTEGER NOT NULL DEFAULT 1,status TEXT NOT NULL DEFAULT 'needs_input',activity TEXT NOT NULL DEFAULT 'Add source material to begin.',assessment TEXT,link TEXT NOT NULL DEFAULT '');
      CREATE INDEX IF NOT EXISTS projects_owner ON projects(user_id,created);
      CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,name TEXT NOT NULL,bytes INTEGER NOT NULL,sha256 TEXT,path TEXT NOT NULL,ready INTEGER NOT NULL DEFAULT 0,created INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,job_id TEXT NOT NULL,source_id TEXT,kind TEXT NOT NULL,sha256 TEXT NOT NULL,content TEXT NOT NULL,created INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,user_id TEXT NOT NULL,revision INTEGER NOT NULL,status TEXT NOT NULL,activity TEXT NOT NULL,created INTEGER NOT NULL,updated INTEGER NOT NULL,lease_until INTEGER,attempts INTEGER NOT NULL DEFAULT 0,error TEXT);
      CREATE UNIQUE INDEX IF NOT EXISTS one_active_job ON jobs(project_id) WHERE status IN ('queued','running');
      CREATE TABLE IF NOT EXISTS attempts(key TEXT NOT NULL,at INTEGER NOT NULL);
      CREATE INDEX IF NOT EXISTS attempts_key ON attempts(key,at);`);
    if (
      !this.all("PRAGMA table_info(projects)").some(
        (column) => column.name === "create_key",
      )
    )
      this.db.exec("ALTER TABLE projects ADD COLUMN create_key TEXT");
    this.db.exec(
      "CREATE UNIQUE INDEX IF NOT EXISTS project_creation_key ON projects(user_id,create_key)",
    );
  }
  run(sql, ...args) {
    return this.db.prepare(sql).run(...args);
  }
  get(sql, ...args) {
    return this.db.prepare(sql).get(...args);
  }
  all(sql, ...args) {
    return this.db.prepare(sql).all(...args);
  }
  transaction(fn) {
    this.db.exec("BEGIN IMMEDIATE");
    try {
      const result = fn();
      this.db.exec("COMMIT");
      return result;
    } catch (error) {
      this.db.exec("ROLLBACK");
      throw error;
    }
  }
  owner(userId, id) {
    return this.get(
      "SELECT * FROM projects WHERE id=? AND user_id=?",
      id,
      userId,
    );
  }
  file(userId, projectId, fileId) {
    return this.get(
      "SELECT files.* FROM files JOIN projects ON projects.id=files.project_id WHERE files.id=? AND files.project_id=? AND projects.user_id=?",
      fileId,
      projectId,
      userId,
    );
  }
  detail(row, includeEvidence = false) {
    const { user_id: _owner, assessment, ...project } = row;
    return {
      ...project,
      assessment: assessment ? JSON.parse(assessment) : null,
      files: this.all(
        "SELECT id,name,bytes,sha256,created FROM files WHERE project_id=? AND ready=1 ORDER BY created",
        row.id,
      ),
      evidence: this.all(
        `SELECT id,source_id,kind,sha256,${includeEvidence ? "content," : ""}created FROM evidence WHERE project_id=? ORDER BY created`,
        row.id,
      ).map((e) => ({
        ...e,
        ...(includeEvidence ? { content: JSON.parse(e.content) } : {}),
      })),
      job:
        this.get(
          "SELECT id,status,activity,created,updated,error,attempts FROM jobs WHERE project_id=? ORDER BY created DESC LIMIT 1",
          row.id,
        ) || null,
    };
  }
  queue(userId, projectId) {
    return this.transaction(() => {
      const p = this.owner(userId, projectId);
      if (!p)
        throw Object.assign(new Error("Project not found."), { status: 404 });
      if (
        this.get(
          "SELECT id FROM files WHERE project_id=? AND ready=0",
          projectId,
        )
      )
        throw Object.assign(
          new Error(
            "Wait for source uploads to finish before starting an assessment.",
          ),
          { status: 409 },
        );
      if (
        !this.get(
          "SELECT id FROM files WHERE project_id=? AND ready=1",
          projectId,
        )
      )
        throw Object.assign(
          new Error(
            "Add at least one source file before starting an evidence-backed assessment.",
          ),
          { status: 409 },
        );
      if (
        this.get(
          "SELECT id FROM jobs WHERE user_id=? AND status IN ('queued','running')",
          userId,
        )
      )
        throw Object.assign(
          new Error(
            "An assessment is already active. Let it finish or cancel it first.",
          ),
          { status: 409 },
        );
      if (
        this.get(
          "SELECT count(*) AS n FROM jobs WHERE user_id=? AND created>?",
          userId,
          Date.now() - 86400000,
        ).n >= 10
      )
        throw Object.assign(
          new Error("The daily free assessment limit has been reached."),
          { status: 429 },
        );
      if (
        this.get(
          "SELECT count(*) AS n FROM jobs WHERE status IN ('queued','running')",
        ).n >= 100
      )
        throw Object.assign(
          new Error("The investigation queue is full. Please try again later."),
          { status: 503 },
        );
      const now = Date.now(),
        id = randomUUID();
      this.run(
        "INSERT INTO jobs(id,project_id,user_id,revision,status,activity,created,updated) VALUES(?,?,?,?,'queued','Waiting for an analysis workspace',?,?)",
        id,
        projectId,
        userId,
        p.revision,
        now,
        now,
      );
      this.run(
        "UPDATE projects SET status='queued',activity='Waiting for an analysis workspace' WHERE id=?",
        projectId,
      );
      return id;
    });
  }
  claim(timeout) {
    return this.transaction(() => {
      const now = Date.now();
      const expired = this.all(
        "SELECT * FROM jobs WHERE status='running' AND lease_until<?",
        now,
      );
      for (const job of expired) {
        const retry = job.attempts < 2;
        this.run(
          "UPDATE jobs SET status=?,activity=?,updated=?,error=? WHERE id=?",
          retry ? "queued" : "failed",
          retry
            ? "Restoring saved inputs after an interruption"
            : "Assessment interrupted",
          now,
          "The previous analysis workspace did not finish. Completed evidence is preserved.",
          job.id,
        );
        this.run(
          "UPDATE projects SET status=?,activity=? WHERE id=?",
          retry ? "queued" : "failed",
          retry
            ? "Restoring saved inputs after an interruption"
            : "Assessment interrupted; retry is available.",
          job.project_id,
        );
      }
      const job = this.get(
        "SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1",
      );
      if (!job) return null;
      this.run(
        "UPDATE jobs SET status='running',attempts=attempts+1,lease_until=?,updated=? WHERE id=?",
        now + timeout + 30000,
        now,
        job.id,
      );
      this.run(
        "UPDATE projects SET status='running',activity='Preparing an isolated analysis workspace' WHERE id=?",
        job.project_id,
      );
      return { ...job, attempts: job.attempts + 1 };
    });
  }
  close() {
    this.db.close();
  }
}
