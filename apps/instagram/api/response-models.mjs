import {createHash} from 'node:crypto';

export function applyResponseModels(paths, components, contracts, normalize, apkSha256) {
  if (contracts.source_apk_sha256 !== apkSha256) throw new Error('Response evidence differs from target APK');
  const references = new Map();
  for (const [type, parser] of Object.entries(contracts.parsers)) {
    if (!parser.recognized_fields.length) continue;
    const name = 'PartialResponse_' + createHash('sha256').update(type).digest('hex').slice(0, 12);
    components.schemas[name] = {type: 'object', additionalProperties: true,
      description: 'Partial client JSON-parser model. Property names are compared against a key read from the input reader. Wire value types, nullability, nested structures, requiredness and server status codes remain unresolved. Unobserved fields are allowed.',
      'x-parser-method': parser.method, 'x-dex-sha256': parser.dex_sha256,
      properties: Object.fromEntries(parser.recognized_fields.map(field => [field.name, {
        description: 'Recognized client parser key. Value schema and server requiredness unknown. Client reader calls, when present, describe an exclusive matched branch; Java return descriptors are not JSON wire types.', 'x-evidence': field.evidence,
        ...(field.client_reader_calls?.length ? {'x-client-reader-calls':field.client_reader_calls} : {}),
      }]))};
    references.set(type, {$ref: '#/components/schemas/' + name});
  }
  // Link reviewed child-parser models as client evidence only. JSON wire schemas
  // stay open: a client may accept/coerce tokens beyond its Java return type.
  for (const [type, parser] of Object.entries(contracts.parsers)) {
    const model = references.get(type);
    if (!model) continue;
    const properties = components.schemas[model.$ref.split('/').at(-1)].properties;
    for (const field of parser.recognized_fields) {
      const nested = [...new Set((field.client_reader_calls ?? []).map(call => call.nested_parser).filter(Boolean))];
      const models = nested.filter(type => references.has(type)).map(type => references.get(type));
      if (models.length) properties[field.name]['x-client-nested-response-models'] = models;
    }
  }
  const grouped = new Map();
  for (const entry of contracts.operations) {
    const normalized = normalize(entry.path), method = entry.method.toLowerCase();
    const operation = normalized && paths[normalized.path]?.[method];
    if (!operation) throw new Error('Response evidence references an undocumented operation');
    if (!grouped.has(operation)) grouped.set(operation, []);
    grouped.get(operation).push(...entry.parsers);
  }
  for (const [operation, parsers] of grouped) {
    operation['x-response-parser-evidence'] ??= [];
    operation['x-recovered-response-fields'] ??= [];
    for (const parser of parsers) {
      operation['x-response-parser-evidence'].push(parser);
      for (const field of contracts.parsers[parser.type]?.recognized_fields ?? []) {
        const existing=operation['x-recovered-response-fields'].find(value=>value.name===field.name);
        if (!existing) operation['x-recovered-response-fields'].push(structuredClone(field));
        else {
          existing.evidence=[...new Map([...existing.evidence,...field.evidence].map(item=>[JSON.stringify(item),item])).values()];
          existing.client_reader_calls=[...new Map([...(existing.client_reader_calls??[]),...(field.client_reader_calls??[])].map(item=>[JSON.stringify(item),item])).values()];
        }
      }
    }
    const models = [...new Map(parsers.filter(parser => references.has(parser.type)).map(parser => [parser.type, references.get(parser.type)])).values()];
    if (!models.length) continue;
    operation['x-response-models'] = models;
    const response = operation.responses.default ??= {description: 'Client response; server status codes unknown.'};
    // Preserve manually traced response schemas instead of replacing them with
    // a weaker automatically recovered model.
    if (!response.content) {
      response.content = {'application/json': {schema: models.length === 1 ? models[0] : {anyOf: models}}};
      response.description = 'Partial client parser model. HTTP status codes, wire Content-Type, field types and requiredness unverified.';
      response['x-media-type-status'] = 'Inferred from JSON parser; wire Content-Type unverified';
    }
    operation.description += '\n\n**Recognized response fields (partial):** ' + operation['x-recovered-response-fields'].map(field => '`' + field.name + '`').join(', ') + '. Unknown fields are allowed; value types, requiredness, nested shapes and server error contracts remain unresolved.';
  }
  const errors = new Map();
  for (const entry of contracts.error_operations ?? []) {
    const normalized = normalize(entry.path), operation = normalized && paths[normalized.path]?.[entry.method.toLowerCase()];
    if (!operation) throw new Error('Error parser evidence references an undocumented operation');
    if (!errors.has(operation)) errors.set(operation, []);
    errors.get(operation).push(...entry.parsers);
  }
  const commonError = references.get('LX/01pP;');
  for (const [operation, parsers] of errors) {
    operation['x-error-parser-evidence'] = parsers;
    operation['x-error-dispatch'] = {condition: 'HTTP status >= 400', specialStatus: 403,
      applicability: 'Recovered factory and shared client dispatcher; later overrides and actual server status sets remain unverified.'};
    const models = [...new Map(parsers.filter(parser => references.has(parser.type)).map(parser => [parser.type, references.get(parser.type)])).values()];
    operation['x-error-response-models'] = models;
    const response = schema => ({description: 'The shared client attempts error parsing with this partial model. This does not establish which statuses the server emits, guarantee JSON, or describe every error condition.',
      'x-contract-scope': 'client-error-dispatch', 'x-media-type-status': 'Inferred from client parser; server Content-Type unverified',
      content: {'application/json': {schema}}});
    if (models.length) for (const range of ['4XX', '5XX']) operation.responses[range] ??= response(models.length === 1 ? models[0] : {anyOf: models});
    if (commonError) operation.responses['403'] ??= {...response(commonError),
      description: 'Special client HTTP 403 path: attempt common-response parsing, invoke the error handler, then throw a status-bearing exception. Server payload and status availability remain unverified.'};
  }
}
