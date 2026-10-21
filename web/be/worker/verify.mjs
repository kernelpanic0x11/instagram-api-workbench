import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { spawn } from "node:child_process";

// Inspect a binary supplied by the base image. Never execute the target.
const input = readFileSync("/usr/bin/true");
const child = spawn("node", ["/opt/worker/entry.mjs", "inspect-artifact"], {
  stdio: ["pipe", "pipe", "inherit"],
});
const output = [];
let bytes = 0;
child.stdout.on("data", (chunk) => {
  bytes += chunk.length;
  if (bytes > 524288) child.kill("SIGKILL");
  else output.push(chunk);
});
const timeout = setTimeout(() => child.kill("SIGKILL"), 30000);
const completed = new Promise((resolve, reject) => {
  child.once("error", reject);
  child.once("close", resolve);
});
child.stdin.end(input);
try {
  assert.equal(await completed, 0, "REA inspection must succeed");
  const evidence = JSON.parse(Buffer.concat(output).toString());
  assert.equal(evidence.operation, "inspect_artifact");
  assert.equal(evidence.subject.format, "elf");
  assert.equal(evidence.confidence, "observed");
  assert.equal(evidence.subject.digest.sha256, createHash("sha256").update(input).digest("hex"));
  assert.ok(evidence.evidence_id);
  assert.ok(evidence.limitations.length);
  process.stdout.write(JSON.stringify({
    status: "passed",
    operation: evidence.operation,
    format: evidence.subject.format,
    sha256: evidence.subject.digest.sha256,
    evidenceId: evidence.evidence_id,
    limitations: evidence.limitations,
    targetExecuted: false,
  }, null, 2) + "\n");
} finally {
  clearTimeout(timeout);
}
