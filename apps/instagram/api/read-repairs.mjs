// Reviewed parameter facts remain separate from server acceptance and live checks.
export function applyReadRepairs(paths, contracts, evidence, apkHash) {
  if (!contracts || !evidence?.methods) return;
  if (contracts.source_apk_sha256 !== apkHash || evidence.source_apk_sha256 !== apkHash) throw new Error('Read-repair APK provenance mismatch');
  for (const entry of contracts.operations) {
    const operation = paths[entry.path]?.[entry.method];
    if (!operation || entry.method !== 'get' || !evidence.methods[entry.caller] || !evidence.reviewed_routes.includes(entry.path)) throw new Error('Read-repair caller evidence missing');
    operation['x-reviewed-request-contract'] = {...entry, scope: 'pinned-client-construction', evidence: 'bulk-trace/read-repair-evidence.json'};
    operation.description += '\n\n**Focused request review:** ' + entry.finding;
    operation.parameters ??= [];
    for (const field of entry.fields) {
      if (operation.parameters.some(parameter => parameter.in === 'query' && parameter.name === field.name)) continue;
      operation.parameters.push({name: field.name, in: 'query', required: false, schema: {type: 'string'}, description: 'Client presence: ' + field.client_presence + '. Encoding: ' + field.encoding + '. Server requiredness unknown.', 'x-requiredness-status': 'unknown'});
    }
  }
}
