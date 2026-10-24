import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {coverageLedger, operationReadiness, HTTP_METHODS} from './operation-coverage.mjs';

test('generic editors do not imply recovered fields, response models or live success', () => {
  const readiness = operationReadiness({requestBody: {content: {'application/json': {schema: {}}}}, responses: {default: {description: 'Unknown'}}});
  assert.equal(readiness.request, 'unresolved');
  assert.equal(readiness.response, 'unresolved');
  assert.equal(readiness.live, 'not-tested');
  assert.equal(readiness.contract, 'partial');
});

test('coverage accounts for multiple methods, unresolved paths and independent evidence levels', () => {
  const ledger = coverageLedger({'/example/': {get: {operationId: 'exampleGet', 'x-method-evidence': [{}]},
    post: {operationId: 'examplePost', 'x-recovered-request-fields': [{name: 'synthetic'}], 'x-live-check': {httpStatus: 200}}}, '/unknown/': {'x-method-status': 'unknown'}});
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
