function fieldParameter(field) {
  return {name: field.name, in: 'query', required: false, schema: {type: 'string'},
    description: 'Recovered client parameter. Server requiredness is unknown. Client presence: ' + (field.client_presence_rules ?? []).join(', ') + '. Serialization: ' + (field.client_serializations ?? []).join(', ') + '.',
    'x-requiredness-status': 'unknown', 'x-evidence': field.evidence};
}

export function applyRequestTransports(paths, entries, normalize) {
  const grouped = new Map();
  for (const entry of entries) {
    const normalized = normalize(entry.path), method = entry.method.toLowerCase();
    const operation = normalized && paths[normalized.path]?.[method];
    if (!operation) throw new Error('Transport evidence references an undocumented operation');
    if (!grouped.has(operation)) grouped.set(operation, {method, variants: []});
    grouped.get(operation).variants.push(...entry.variants);
  }
  for (const [operation, {method, variants}] of grouped) {
    if (!variants.length || !['get', 'post'].includes(method) || variants.some(variant => variant.status !== 'client-finalization-traced' || !['plain', 'signed'].includes(variant.envelope) || variant.parameter_location !== (method === 'get' ? 'query' : 'form-body'))) throw new Error('Invalid transport evidence');
    operation['x-request-transport'] = variants;
    const fields = operation['x-recovered-request-fields'] ?? [];
    const signed = variants.some(variant => variant.envelope === 'signed');
    const plain = variants.some(variant => variant.envelope === 'plain');
    const signedField = {type: 'string', pattern: '^SIGNATURE\\.',
      description: 'Client envelope: literal SIGNATURE. followed by serialized JSON parameters. This branch is not a cryptographic signature calculation. Additional integrity/authentication requirements remain unresolved.'};
    if (method === 'get') {
      operation.parameters ??= [];
      const candidates = plain ? fields.map(fieldParameter) : [];
      if (signed) candidates.push({name: 'signed_body', in: 'query', required: false, schema: signedField, 'x-requiredness-status': 'unknown', description: signedField.description});
      for (const parameter of candidates) if (!operation.parameters.some(existing => existing.in === parameter.in && existing.name === parameter.name)) operation.parameters.push(parameter);
    } else if (!operation.requestBody || operation.requestBody.description?.startsWith('Manual payload editor.')) {
      const schemas = [];
      if (plain) schemas.push({type: 'object', additionalProperties: {type: 'string'}, properties: Object.fromEntries(fields.map(field => [field.name, {type: 'string', 'x-client-presence': field.client_presence_rules, 'x-client-serialization': field.client_serializations}]))});
      if (signed) schemas.push({type: 'object', additionalProperties: {type: 'string'}, properties: {signed_body: signedField}, 'x-client-emitted-fields': ['signed_body']});
      operation.requestBody = {required: false,
        description: 'Client-finalization-traced UTF-8 form encoding. This is a partial client construction, not a complete server contract. Requiredness and unobserved fields remain unknown. For a signed envelope, place logical fields inside the signed_body JSON payload. Distinct plain/signed variants reflect separate observed constructions.',
        'x-contract-scope': 'client-construction',
        content: {'application/x-www-form-urlencoded': {schema: schemas.length === 1 ? schemas[0] : {anyOf: schemas}}}};
    }
    operation.description += '\n\n**Client encoding traced through finalization:** ' + [...new Set(variants.map(variant => variant.parameter_location + ' / ' + variant.envelope))].join('; ') + '. Requiredness remains unverified on the server. Traces are bounded to the recorded construction paths.';
  }
}
