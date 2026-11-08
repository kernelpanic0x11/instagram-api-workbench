// A missing or malformed date cannot displace a dated observation. Legacy
// pairs with no usable dates retain their historical last-loaded-wins behavior.
function observationTimestamp(check) {
  for (const value of [check?.checkedAt, check?.checkedOn]) {
    if (typeof value !== 'string') continue;
    const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value);
    const timestamp = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value);
    if (!dateOnly && !timestamp) continue;
    // Date-only legacy checks use the UTC start of that day. A precise
    // timestamp later on the same day takes precedence over the coarse date.
    const parsed = Date.parse(value);
    if (!Number.isFinite(parsed)) continue;
    // Date.parse normalizes impossible calendar dates, such as February 30.
    // Compare the date portion independently before trusting the timestamp.
    const date = value.slice(0, 10);
    if (new Date(Date.parse(date)).toISOString().slice(0, 10) !== date) continue;
    return parsed;
  }
  return null;
}

function latestObservation(existing, incoming) {
  if (!incoming) return existing;
  if (!existing) return incoming;
  const previousTime = observationTimestamp(existing), incomingTime = observationTimestamp(incoming);
  if (incomingTime !== null && previousTime !== null) return incomingTime > previousTime ? incoming : existing;
  if (incomingTime !== null) return incoming;
  if (previousTime !== null) return existing;
  return incoming;
}

// Runtime evidence is independent of full server-contract completeness.
export function applyReadValidation(paths, components, results, apkHash) {
  if (!results) return;
  if (results.source_apk_sha256 !== apkHash) throw new Error('Read-validation APK provenance mismatch');
  for (const check of results.checks) {
    const operation = paths[check.path]?.get;
    if (!operation || check.method !== 'get' || check.rawResponseSaved !== false || check.personalValuesSaved !== false) throw new Error('Invalid read-validation observation');
    const fields = new Set(['status', 'message', 'error_type', ...(operation['x-recovered-response-fields'] ?? []).map(field => field.name)]);
    const kinds = new Set(['string', 'boolean', 'integer', 'number', 'object', 'array', 'null']);
    if (Object.entries(check.fieldTypes ?? {}).some(([name, kind]) => !fields.has(name) || !kinds.has(kind))) throw new Error('Unrecognized response metadata');
    if (check.outcome === 'observed-success' && (check.httpStatus !== 200 || check.instagramStatus !== 'ok' || check.contentType !== 'application/json' || check.bodyKind !== 'object')) throw new Error('Invalid successful read');
    // Retain every observation in ingestion order; the current pointers are
    // selected by observation time, independently of artifact load order.
    (operation['x-read-validation-history'] ??= []).push(check);
    const previousLatest = latestObservation(operation['x-read-validation'], operation['x-live-check']);
    operation['x-read-validation'] = latestObservation(previousLatest, check);
    operation.description = (operation.description ?? '') + '\n\n**Read validation:** HTTP ' + (check.httpStatus ?? 'unavailable') + ', ' + check.outcome + '. This records one tested construction; unverified reads may need parameters, headers or feature access. No response values were retained.';
    if (check.outcome !== 'observed-success') {
      if (Number.isInteger(check.httpStatus)) operation.responses[String(check.httpStatus)] ??= {
        description: 'Observed response for the tested read; application success was not verified. Content type: ' + (check.contentType ?? 'unknown') + '. Body values discarded; error causes and alternate responses remain unresolved.',
        'x-contract-scope': 'observed-unsuccessful-read',
      };
      continue;
    }
    // A newer failure can be the latest attempt while the most recent
    // successful profile and its schema remain available as historical evidence.
    if (latestObservation(operation['x-live-check'], check) !== check) continue;
    operation['x-live-check'] = {...check, scope: 'One authenticated read returned HTTP 200 and JSON status ok. No account values retained. Does not establish complete contracts or feature permissions.'};
    const name = 'ObservedRead_' + operation.operationId.replace(/[^A-Za-z0-9_]/g, '_');
    components.schemas[name] = {
      type: 'object', additionalProperties: true, 'x-contract-scope': 'observed-success-profile',
      description: 'Allowlisted field types observed in one authenticated status-ok response. Field presence, nullability and item types are not universal constraints; unrecognized fields remain open.',
      properties: Object.fromEntries(Object.entries(check.fieldTypes).map(([field, type]) => [field,
        type === 'array' ? {type, items: {}, 'x-observed-item-types': check.arrayItemTypes?.[field] ?? []} :
        field === 'status' ? {type: 'string', const: 'ok'} : {type}])),
    };
    const model = {$ref: '#/components/schemas/' + name};
    operation['x-observed-success-model'] = model;
    if (!operation.responses['200'] || operation.responses['200']['x-contract-scope'] === 'observed-unsuccessful-read') operation.responses['200'] = {description: 'Observed HTTP 200 JSON status-ok response. Inspect application status: HTTP 200 alone does not establish success. Other response variants remain open.', content: {'application/json': {schema: {anyOf: [model, {type: 'object', additionalProperties: true, required: ['status'], properties: {status: {const: 'fail'}}}]}}}};
  }
}
