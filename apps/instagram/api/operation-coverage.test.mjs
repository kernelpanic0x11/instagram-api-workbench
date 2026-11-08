import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {filterCoverageEntries} from './coverage-ui.mjs';
import {coverageLedger, operationReadiness, HTTP_METHODS, CONTRACT_DIMENSIONS} from './operation-coverage.mjs';

test('generic editors do not imply recovered fields, response models or live success', () => {
  const readiness = operationReadiness({requestBody: {content: {'application/json': {schema: {}}}}, responses: {default: {description: 'Unknown'}}});
  assert.equal(readiness.request, 'unresolved');
  assert.equal(readiness.response, 'unresolved');
  assert.equal(readiness.live, 'not-tested');
  assert.equal(readiness.contract, 'partial');
});

test('coverage accounts for multiple methods, unresolved paths and independent evidence levels', () => {
  const ledger = coverageLedger({'/example/': {get: {operationId: 'exampleGet', 'x-method-evidence': [{}]},
    post: {operationId: 'examplePost', 'x-recovered-request-fields': [{name: 'synthetic'}], 'x-live-check': {httpStatus: 200, instagramStatus: 'ok'}}}, '/unknown/': {'x-method-status': 'unknown'}});
  assert.deepEqual(ledger.operations.map(operation => operation.method), ['get', 'post']);
  assert.equal(ledger.summary.documentedOperations, 2);
  assert.equal(ledger.summary.unresolvedMethodPaths, 1);
  assert.equal(ledger.summary.operationsWithRecoveredFields, 1);
  assert.equal(ledger.summary.liveSuccessObservations, 1);
  assert.equal(ledger.summary.completeContracts, 0);
  assert.equal(ledger.operations[1].response, 'unresolved');
});

test('every generated Swagger operation appears exactly once in the downloadable ledger', () => {
  const read = name => JSON.parse(fs.readFileSync(new URL(name, import.meta.url)));
  const spec = read('openapi.json'), ledger = read('coverage.json');
  const expected = Object.entries(spec.paths).flatMap(([path, item]) => HTTP_METHODS.filter(method => item[method]).map(method => method + ' ' + path)).sort();
  const actual = ledger.operations.map(operation => operation.method + ' ' + operation.path).sort();
  assert.deepEqual(actual, expected);
  assert.equal(new Set(actual).size, actual.length);
  assert.equal(ledger.summary.documentedOperations, spec['x-coverage'].documentedOperations);
  assert.ok(actual.length > 600);
  for (const operation of ledger.operations) {
    assert.equal(operation.contract, 'partial');
    for (const field of spec.paths[operation.path][operation.method]['x-recovered-request-fields'] ?? []) {
      assert.equal(field.required_status, 'unknown');
      assert.ok(field.evidence.length);
      assert.ok(field.evidence.every(evidence => Number.isInteger(evidence.dex_byte_offset) && evidence.caller));
    }
  }
});


test('HTTP 200 and a success label without application success do not prove a live read', () => {
  for (const check of [
    {httpStatus: 200},
    {httpStatus: 200, instagramStatus: 'fail', outcome: 'observed-success'},
    {httpStatus: 200, instagramStatus: 'ok', contentType: 'text/html'},
    {httpStatus: 200, instagramStatus: 'ok', outcome: 'http-error'},
  ]) {
    const readiness = operationReadiness({'x-live-check': check});
    assert.equal(readiness.live, 'not-verified');
    assert.equal(readiness.successCheckedAt, null);
    assert.equal(readiness.fullyOperationalVerified, false);
  }
});

test('historical success remains visible when the latest retest fails', () => {
  const operation = {
    'x-live-check': {httpStatus: 200, instagramStatus: 'ok', checkedOn: '2026-10-20'},
    'x-read-validation': {httpStatus: 400, instagramStatus: 'fail', checkedAt: '2026-10-21T00:00:00Z'},
  };
  const ledger = coverageLedger({'/example/': {get: operation}}), readiness = operation['x-readiness'];
  assert.equal(readiness.live, 'observed-success');
  assert.equal(readiness.latestLiveOutcome, 'not-verified');
  assert.equal(readiness.testedHttpStatus, 400);
  assert.equal(readiness.successCheckedAt, '2026-10-20');
  assert.equal(readiness.latestCheckedAt, '2026-10-21T00:00:00Z');
  assert.equal(ledger.summary.historicalSuccessWithLatestFailure, 1);
  assert.equal(ledger.summary.liveSuccessObservations, 1);
  assert.equal(filterCoverageEntries(ledger, 'failed').length, 1);
});

test('a transport failure is an attempted read even without an HTTP response', () => {
  const ledger = coverageLedger({'/example/': {get: {'x-read-validation': {httpStatus: null, outcome: 'transport-error'}}}});
  assert.equal(ledger.summary.attemptedReadOperations, 1);
  assert.equal(ledger.summary.latestUnsuccessfulReadObservations, 1);
  assert.equal(ledger.summary.liveSuccessObservations, 0);
});

test('recovered client construction and live success preserve unproven contract dimensions', () => {
  const readiness = operationReadiness({
    'x-method-evidence': [{}], 'x-request-contract': {scope: 'pinned-client-construction'},
    'x-request-transport': [{parameter_location: 'query', envelope: 'plain', root_path_override: true}],
    'x-recovered-response-fields': [{name: 'message', client_reader_calls: [{}]}],
    'x-error-parser-evidence': [{}], 'x-live-check': {httpStatus: 200, instagramStatus: 'ok'},
    'x-focused-contract': {status: 'client-profile-traced', remaining: ['Synthetic unresolved wire variant']},
    responses: {200: {content: {'application/json': {schema: {$ref: '#/components/schemas/Synthetic'}}}}},
  });
  assert.equal(readiness.contract, 'partial');
  assert.equal(readiness.fullyOperationalVerified, false);
  assert.equal(readiness.contractDimensions.authentication, 'observed-session-profile');
  assert.equal(readiness.contractDimensions.signing, 'client-envelope-traced');
  assert.equal(readiness.contractDimensions.errorResponses, 'client-parser-bound');
  assert.equal(readiness.contractDimensions.messageTypes, 'partial-field-evidence');
  assert.equal(readiness.contractDimensions.requiredness, 'unresolved');
  assert.ok(readiness.unresolvedDimensions.includes('requiredness'));
  assert.ok(readiness.partialDimensions.includes('authentication'));
  assert.ok(readiness.partialDimensions.includes('responseSchema'));
  assert.equal(readiness.rootRelativeClientVariant, true);
  assert.deepEqual(readiness.focusedRemainingGaps, ['Synthetic unresolved wire variant']);
});

test('empty success response editors do not count as recovered response schemas', () => {
  for (const schema of [{}, {type: 'object', additionalProperties: true}, {type: 'array', items: {}}]) {
    assert.equal(operationReadiness({responses: {200: {content: {'application/json': {schema}}}}}).response, 'unresolved');
  }
  assert.equal(operationReadiness({responses: {200: {content: {'application/json': {schema: {anyOf: [{$ref: '#/components/schemas/Synthetic'}, {}]}}}}}}).response, 'partial-model');
});

test('unknown-method candidates retain dimension gaps and cannot become executable operations', () => {
  const paths = {'/unknown/{arg1}/': {'x-evidence': [{kind: 'route_candidate'}]}, '/known/': {get: {'x-method-evidence': [{}]}}};
  const ledger = coverageLedger(paths);
  assert.equal(ledger.operations.length, 1);
  assert.equal(ledger.unresolvedPaths.length, 1);
  assert.equal(ledger.unresolvedPaths[0].method, null);
  assert.equal(ledger.unresolvedPaths[0].evidenceCount, 1);
  assert.equal(ledger.unresolvedPaths[0].contract, 'unresolved');
  assert.deepEqual(ledger.unresolvedPaths[0].unresolvedDimensions, Object.keys(CONTRACT_DIMENSIONS));
  assert.equal(paths['/unknown/{arg1}/']['x-readiness'].methodEvidence, 'unresolved');
  assert.deepEqual(paths['/unknown/{arg1}/']['x-readiness'].unresolvedDimensions, Object.keys(CONTRACT_DIMENSIONS));
  assert.ok(HTTP_METHODS.every(method => paths['/unknown/{arg1}/'][method] === undefined));
  assert.equal(filterCoverageEntries(ledger, 'all').length, 2);
  assert.equal(filterCoverageEntries(ledger, 'methods', 'UNKNOWN').length, 1);
  assert.equal(filterCoverageEntries(ledger, 'dimension:requiredness').length, 2);
  assert.equal(filterCoverageEntries(ledger, 'live').length, 0);
});

test('dimension counts and unresolved paths cover the generated spec without inferring completeness', () => {
  const spec = JSON.parse(fs.readFileSync(new URL('openapi.json', import.meta.url)));
  const ledger = coverageLedger(spec.paths);
  const pathSet = new Set([...ledger.operations, ...ledger.unresolvedPaths].map(entry => entry.path));
  assert.deepEqual([...pathSet].sort(), Object.keys(spec.paths).sort());
  assert.equal(ledger.summary.completeContracts, 0);
  assert.equal(ledger.summary.fullyOperationalVerifiedContracts, 0);
  for (const operation of ledger.operations) {
    assert.deepEqual(Object.keys(operation.contractDimensions), Object.keys(CONTRACT_DIMENSIONS));
    assert.ok(operation.unresolvedDimensions.includes('requiredness'));
    assert.equal(operation.fullyOperationalVerified, false);
  }
  assert.equal(ledger.summary.operationsByUnresolvedDimension.requiredness, ledger.operations.length);
});
