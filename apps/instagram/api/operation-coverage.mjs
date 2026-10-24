export const HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete', 'options', 'head', 'trace'];

// A static method, a partial logical model and a live response are separate
// evidence levels. None implies that an entire request contract is recovered.
export function operationReadiness(operation) {
  const fields = operation['x-recovered-request-fields'] ?? [];
  const responseModel = Object.entries(operation.responses ?? {}).some(([status, response]) =>
    (status === 'default' || /^2(?:\d\d|XX)$/.test(status)) && Object.values(response.content ?? {}).some(media => media.schema));
  return {
    methodEvidence: operation['x-method-evidence']?.length ? 'static-traced' : 'unresolved',
    focusedContract: operation['x-focused-contract']?.status ?? null,
    request: operation['x-request-contract'] ? 'client-construction-traced' : fields.length ? 'partial-fields' : operation['x-request-model'] || operation['x-request-fields'] ? 'partial-model' : 'unresolved',
    recoveredFieldCount: fields.length,
    response: responseModel ? 'partial-model' : 'unresolved',
    responseParserBound: !!operation['x-response-parser-evidence']?.length,
    recoveredResponseFieldCount: operation['x-recovered-response-fields']?.length ?? 0,
    responseFieldsWithReaderCalls: (operation['x-recovered-response-fields']??[]).filter(field=>field.client_reader_calls?.length).length,
    encoding: operation['x-request-transport']?.length ? 'client-finalization-traced' : 'unresolved',
    transportVariants: [...new Set((operation['x-request-transport'] ?? []).map(variant => variant.parameter_location + '/' + variant.envelope))],
    errorParserBound: !!operation['x-error-parser-evidence']?.length,
    live: operation['x-live-check'] ? 'observed-success' : operation['x-read-validation'] ? 'not-verified' : 'not-tested',
    testedHttpStatus: operation['x-read-validation']?.httpStatus ?? null,
    contract: 'partial',
  };
}

export function coverageLedger(paths) {
  const operations = [];
  let unresolvedPaths = 0;
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
    if (!count) unresolvedPaths++;
  }
  operations.sort((left, right) => left.path.localeCompare(right.path) || HTTP_METHODS.indexOf(left.method) - HTTP_METHODS.indexOf(right.method));
  return {summary: {
    documentedOperations: operations.length, unresolvedMethodPaths: unresolvedPaths,
    operationsWithRecoveredFields: operations.filter(operation => operation.recoveredFieldCount > 0).length,
    recoveredFieldsByOperation: operations.reduce((sum, operation) => sum + operation.recoveredFieldCount, 0),
    operationsWithPartialResponseModels: operations.filter(operation => operation.response === 'partial-model').length,
    operationsWithResponseParserBindings: operations.filter(operation => operation.responseParserBound).length,
    recoveredResponseFieldsByOperation: operations.reduce((sum, operation) => sum + operation.recoveredResponseFieldCount, 0),
    operationsWithResponseReaderCalls: operations.filter(operation=>operation.responseFieldsWithReaderCalls>0).length,
    responseFieldsWithReaderCallsByOperation: operations.reduce((sum,operation)=>sum+operation.responseFieldsWithReaderCalls,0),
    operationsWithFinalizedEncoding: operations.filter(operation => operation.encoding === 'client-finalization-traced').length,
    operationsWithErrorParserBindings: operations.filter(operation => operation.errorParserBound).length,
    liveSuccessObservations: operations.filter(operation => operation.live === 'observed-success').length,
    attemptedReadOperations: operations.filter(operation => operation.testedHttpStatus !== null).length,
    unsuccessfulReadObservations: operations.filter(operation => operation.live === 'not-verified').length,
    completeContracts: 0,
  }, operations};
}
