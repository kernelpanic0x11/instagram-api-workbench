export const HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete', 'options', 'head', 'trace'];

// These dimensions describe the evidence needed for a complete contract. A
// traced client branch or a successful request covers only the recorded profile.
export const CONTRACT_DIMENSIONS = {
  methodAndRoute: 'HTTP method and route',
  requestFields: 'Complete request fields and conditional branches',
  requiredness: 'Server required fields, constraints and defaults',
  encoding: 'Request placement and wire encoding',
  authentication: 'Minimum authentication and feature permissions',
  signing: 'Signing and integrity requirements',
  responseSchema: 'Complete response types, variants and nullability',
  messageTypes: 'Message variants and semantics',
  errorResponses: 'Server error statuses, shapes and triggering conditions',
  liveValidation: 'Live behavior across supported request profiles',
};

function hasResponseSchema(schema) {
  if (!schema || typeof schema !== 'object') return false;
  if (schema.$ref || Object.keys(schema.properties ?? {}).length) return true;
  if (['anyOf', 'oneOf', 'allOf'].some(key => schema[key]?.some(hasResponseSchema))) return true;
  return schema.type && !['object', 'array'].includes(schema.type) || schema.type === 'array' && hasResponseSchema(schema.items);
}

function isSuccessfulRead(check) {
  return !!check && check.httpStatus === 200 && check.instagramStatus === 'ok' &&
    (check.outcome === undefined || check.outcome === 'observed-success') &&
    (check.contentType === undefined || check.contentType === 'application/json') &&
    (check.bodyKind === undefined || check.bodyKind === 'object');
}

function observationDate(check) {
  return check?.checkedAt ?? check?.checkedOn ?? null;
}

// A static method, a partial logical model and a live response are separate
// evidence levels. None implies that an entire server contract is recovered.
export function operationReadiness(operation) {
  const fields = operation['x-recovered-request-fields'] ?? [];
  const responseFields = operation['x-recovered-response-fields'] ?? [];
  const responseModel = Object.entries(operation.responses ?? {}).some(([status, response]) =>
    (status === 'default' || /^2(?:\d\d|XX)$/.test(status)) && Object.values(response.content ?? {}).some(media => hasResponseSchema(media.schema)));
  const transports = operation['x-request-transport'] ?? [];
  const successfulRead = isSuccessfulRead(operation['x-live-check']) ? operation['x-live-check'] : null;
  const latestRead = operation['x-read-validation'] ?? operation['x-live-check'];
  const methodTraced = !!operation['x-method-evidence']?.length;
  const requestTraced = !!operation['x-request-contract'];
  const errorParserBound = !!operation['x-error-parser-evidence']?.length;
  const dimensions = {
    methodAndRoute: methodTraced ? 'client-traced' : 'unresolved',
    requestFields: requestTraced ? 'client-construction-traced' : fields.length || operation['x-request-model'] || operation['x-request-fields'] ? 'partial' : 'unresolved',
    requiredness: 'unresolved',
    encoding: transports.length ? 'client-finalization-traced' : 'unresolved',
    authentication: successfulRead ? 'observed-session-profile' : 'unresolved',
    signing: transports.length ? 'client-envelope-traced' : 'unresolved',
    responseSchema: responseModel ? 'partial' : 'unresolved',
    messageTypes: responseFields.some(field => ['message', '_messages'].includes(field.name)) ? 'partial-field-evidence' : 'unresolved',
    errorResponses: errorParserBound ? 'client-parser-bound' : 'unresolved',
    liveValidation: successfulRead ? 'observed-request-profile' : latestRead ? 'attempted-not-verified' : 'unresolved',
  };
  return {
    methodEvidence: methodTraced ? 'static-traced' : 'unresolved',
    focusedContract: operation['x-focused-contract']?.status ?? null,
    focusedRemainingGaps: operation['x-focused-contract']?.remaining ?? [],
    request: requestTraced ? 'client-construction-traced' : fields.length ? 'partial-fields' : operation['x-request-model'] || operation['x-request-fields'] ? 'partial-model' : 'unresolved',
    recoveredFieldCount: fields.length,
    response: responseModel ? 'partial-model' : 'unresolved',
    responseParserBound: !!operation['x-response-parser-evidence']?.length,
    recoveredResponseFieldCount: responseFields.length,
    responseFieldsWithReaderCalls: responseFields.filter(field => field.client_reader_calls?.length).length,
    encoding: transports.length ? 'client-finalization-traced' : 'unresolved',
    transportVariants: [...new Set(transports.map(variant => variant.parameter_location + '/' + variant.envelope))],
    rootRelativeClientVariant: transports.some(variant => variant.root_path_override === true),
    errorParserBound,
    live: successfulRead ? 'observed-success' : latestRead ? 'not-verified' : 'not-tested',
    liveAttempted: !!latestRead,
    testedHttpStatus: latestRead?.httpStatus ?? null,
    latestLiveOutcome: latestRead ? isSuccessfulRead(latestRead) ? 'observed-success' : 'not-verified' : 'not-tested',
    latestCheckedAt: observationDate(latestRead),
    successCheckedAt: observationDate(successfulRead),
    contract: 'partial',
    contractDimensions: dimensions,
    unresolvedDimensions: Object.keys(dimensions).filter(name => dimensions[name] === 'unresolved'),
    partialDimensions: Object.keys(dimensions).filter(name => name !== 'methodAndRoute' && dimensions[name] !== 'unresolved'),
    // Requiredness, authentication, unobserved response variants and error
    // conditions are never inferred from client parsers or one status-ok read.
    fullyOperationalVerified: false,
  };
}

export function coverageLedger(paths) {
  const operations = [], unresolvedPaths = [];
  for (const [path, item] of Object.entries(paths)) {
    let count = 0;
    for (const method of HTTP_METHODS) {
      const operation = item[method];
      if (!operation) continue;
      count++;
      const readiness = operationReadiness(operation);
      operation['x-readiness'] = readiness;
      operations.push({path, method, operationId: operation.operationId, tags: operation.tags ?? [], ...readiness,
        fields: (operation['x-recovered-request-fields'] ?? []).map(field => field.name),
        responseFields: (operation['x-recovered-response-fields'] ?? []).map(field => field.name)});
    }
    if (!count) {
      const readiness = {methodEvidence: 'unresolved', live: 'not-tested', contract: 'unresolved', fullyOperationalVerified: false,
        contractDimensions: Object.fromEntries(Object.keys(CONTRACT_DIMENSIONS).map(name => [name, 'unresolved'])),
        unresolvedDimensions: Object.keys(CONTRACT_DIMENSIONS), partialDimensions: []};
      item['x-readiness'] = readiness;
      unresolvedPaths.push({path, method: null, evidenceCount: item['x-evidence']?.length ?? 0, ...readiness});
    }
  }
  operations.sort((left, right) => left.path.localeCompare(right.path) || HTTP_METHODS.indexOf(left.method) - HTTP_METHODS.indexOf(right.method));
  unresolvedPaths.sort((left, right) => left.path.localeCompare(right.path));
  return {
    scope: 'Evidence from the pinned client and bounded historical reads. No fully operational or complete server contract is established. Unknown-method paths are non-executable route candidates.',
    contractDimensionLabels: CONTRACT_DIMENSIONS,
    summary: {
      documentedOperations: operations.length, unresolvedMethodPaths: unresolvedPaths.length,
      operationsWithRecoveredFields: operations.filter(operation => operation.recoveredFieldCount > 0).length,
      recoveredFieldsByOperation: operations.reduce((sum, operation) => sum + operation.recoveredFieldCount, 0),
      operationsWithPartialResponseModels: operations.filter(operation => operation.response === 'partial-model').length,
      operationsWithResponseParserBindings: operations.filter(operation => operation.responseParserBound).length,
      recoveredResponseFieldsByOperation: operations.reduce((sum, operation) => sum + operation.recoveredResponseFieldCount, 0),
      operationsWithResponseReaderCalls: operations.filter(operation => operation.responseFieldsWithReaderCalls > 0).length,
      responseFieldsWithReaderCallsByOperation: operations.reduce((sum, operation) => sum + operation.responseFieldsWithReaderCalls, 0),
      operationsWithFinalizedEncoding: operations.filter(operation => operation.encoding === 'client-finalization-traced').length,
      operationsWithErrorParserBindings: operations.filter(operation => operation.errorParserBound).length,
      liveSuccessObservations: operations.filter(operation => operation.live === 'observed-success').length,
      attemptedReadOperations: operations.filter(operation => operation.liveAttempted).length,
      unsuccessfulReadObservations: operations.filter(operation => operation.live === 'not-verified').length,
      latestUnsuccessfulReadObservations: operations.filter(operation => operation.latestLiveOutcome === 'not-verified').length,
      historicalSuccessWithLatestFailure: operations.filter(operation => operation.live === 'observed-success' && operation.latestLiveOutcome === 'not-verified').length,
      operationsWithRootRelativeClientVariants: operations.filter(operation => operation.rootRelativeClientVariant).length,
      operationsByUnresolvedDimension: Object.fromEntries(Object.keys(CONTRACT_DIMENSIONS).map(name => [name, operations.filter(operation => operation.unresolvedDimensions.includes(name)).length])),
      operationsByPartialDimension: Object.fromEntries(Object.keys(CONTRACT_DIMENSIONS).map(name => [name, operations.filter(operation => operation.partialDimensions.includes(name)).length])),
      completeContracts: 0,
      fullyOperationalVerifiedContracts: 0,
    }, operations, unresolvedPaths,
  };
}
