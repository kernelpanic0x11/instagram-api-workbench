import fs from 'node:fs';
const policy = JSON.parse(fs.readFileSync(new URL('request-header-policy.json',import.meta.url)));
const exactNames = new Set(policy.names);
export function allowedAdditionalHeader(name) {
  const lower = name.toLowerCase();
  if (!/^[a-z0-9-]+$/.test(lower)) return false;
  return exactNames.has(lower) || policy.prefixes.some(prefix => lower.startsWith(prefix) && lower.length > prefix.length);
}
