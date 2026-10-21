import { createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";
import { Readable } from "node:stream";
import { spawn } from "node:child_process";

const operation = process.env.REA_OPERATION || process.argv[2];
if (!["inspect-artifact", "inspect-android-package"].includes(operation))
  throw new Error("Operation is not allowlisted.");
const input = `/work/input${operation === "inspect-android-package" ? ".apk" : ".bin"}`;
const remote = Boolean(process.env.INPUT_URL);
if (remote) {
  const url = new URL(process.env.INPUT_URL);
  if (url.protocol !== "https:" || !url.hostname.endsWith(".amazonaws.com"))
    throw new Error("Invalid artifact storage endpoint.");
  const response = await fetch(url, {
    redirect: "error",
    signal: AbortSignal.timeout(45000),
  });
  if (
    !response.ok ||
    !response.body ||
    Number(response.headers.get("content-length")) > 268435456
  )
    throw new Error("Artifact download failed or exceeds budget.");
  await pipeline(
    Readable.fromWeb(response.body),
    createWriteStream(input, { flags: "wx", mode: 0o600 }),
  );
} else {
  let bytes = 0;
  process.stdin.on("data", (chunk) => {
    bytes += chunk.length;
    if (bytes > 268435456) process.exit(2);
  });
  await pipeline(
    process.stdin,
    createWriteStream(input, { flags: "wx", mode: 0o600 }),
  );
}
const child = spawn(
  "node",
  [
    "/opt/rea/node_modules/rea-agents/scripts/rea.mjs",
    operation,
    input,
    "--json",
  ],
  {
    stdio: ["ignore", "pipe", "pipe"],
    env: {
      PATH: process.env.PATH,
      HOME: "/tmp",
      REA_JADX_MCP_JAR: "/opt/jadx/engine.jar",
    },
  },
);
const out = [],
  errors = [];
let count = 0;
child.stdout.on("data", (chunk) => {
  count += chunk.length;
  if (count > 524288) child.kill("SIGKILL");
  else out.push(chunk);
});
child.stderr.on("data", (chunk) => {
  if (errors.length < 8) errors.push(chunk.subarray(0, 512));
});
const timeout = setTimeout(() => child.kill("SIGKILL"), 150000);
const code = await new Promise((resolve, reject) => {
  child.once("error", reject);
  child.once("close", resolve);
});
clearTimeout(timeout);
if (code !== 0 || count > 524288)
  throw new Error(
    "Static analysis did not complete within its resource budget.",
  );
const body = Buffer.concat(out);
JSON.parse(body.toString());
if (remote) {
  const url = new URL(process.env.OUTPUT_URL);
  if (url.protocol !== "https:" || !url.hostname.endsWith(".amazonaws.com"))
    throw new Error("Invalid evidence storage endpoint.");
  const response = await fetch(url, {
    method: "PUT",
    body,
    headers: {
      "content-type": "application/json",
      "x-amz-server-side-encryption": "AES256",
    },
    redirect: "error",
    signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) throw new Error("Evidence persistence failed.");
} else process.stdout.write(body);
