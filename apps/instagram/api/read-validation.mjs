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
    (operation['x-read-validation-history'] ??= []).push(check);
    operation['x-read-validation'] = check;
    operation.description = (operation.description ?? '') + '\n\n**Read validation:** HTTP ' + (check.httpStatus ?? 'unavailable') + ', ' + check.outcome + '. This records one tested construction; unverified reads may need parameters, headers or feature access. No response values were retained.';
    if (check.outcome !== 'observed-success') {
      if (Number.isInteger(check.httpStatus)) operation.responses[String(check.httpStatus)] ??= {
        description: 'Observed response for the tested read; application success was not verified. Content type: ' + (check.contentType ?? 'unknown') + '. Body values discarded; error causes and alternate responses remain unresolved.',
        'x-contract-scope': 'observed-unsuccessful-read',
      };
      continue;
    }
    if (check.httpStatus !== 200 || check.instagramStatus !== 'ok' || check.contentType !== 'application/json' || check.bodyKind !== 'object') throw new Error('Invalid successful read');
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
