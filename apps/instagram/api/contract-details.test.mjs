import test from 'node:test';
import assert from 'node:assert/strict';
import {applyRequestTransports} from './request-transports.mjs';
import {applySharedModels} from './shared-models.mjs';
import {applyResponseModels} from './response-models.mjs';
import {operationReadiness} from './operation-coverage.mjs';

const normalize = path => ({path: path.split('?')[0]});
const field = {name: 'synthetic_field', evidence: [{}], client_presence_rules: ['omitted-if-null'], client_serializations: ['string-value']};
const transport = (method, envelope) => ({path: '/example/', method, variants: [{status: 'client-finalization-traced', parameter_location: method === 'GET' ? 'query' : 'form-body', envelope}]});
const operation = () => ({description: 'Synthetic', responses: {default: {description: 'Unknown'}}, 'x-recovered-request-fields': [field]});

test('signed POST documents the form envelope without inventing server requiredness', () => {
  const op = operation();
  applyRequestTransports({'/example/': {post: op}}, [transport('POST', 'signed')], normalize);
  const schema = op.requestBody.content['application/x-www-form-urlencoded'].schema;
  assert.equal(op.requestBody.required, false);
  assert.equal(schema.required, undefined);
  assert.deepEqual(Object.keys(schema.properties), ['signed_body']);
  assert.ok(new RegExp(schema.properties.signed_body.pattern).test('SIGNATURE.{}'));
  assert.ok(!new RegExp(schema.properties.signed_body.pattern).test('SIGNATUREx{}'));
  assert.ok(!op.requestBody.content['application/json']);
});

test('plain and signed GET parameters follow their distinct envelope rules', () => {
  const plain = operation(), signed = operation();
  plain.parameters = [{name: 'arg1', in: 'path', required: true}];
  applyRequestTransports({'/example/': {get: plain}}, [transport('GET', 'plain')], normalize);
  applyRequestTransports({'/example/': {get: signed}}, [transport('GET', 'signed')], normalize);
  assert.equal(plain.parameters[0].in, 'path');
  assert.equal(plain.parameters[1].name, 'synthetic_field');
  assert.equal(plain.parameters[1]['x-requiredness-status'], 'unknown');
  assert.deepEqual(signed.parameters.map(parameter => parameter.name), ['signed_body']);
});

test('multiple observed envelopes remain alternatives and invalid evidence is rejected', () => {
  const op = operation();
  applyRequestTransports({'/example/': {post: op}}, [transport('POST', 'plain'), transport('POST', 'signed')], normalize);
  assert.equal(op.requestBody.content['application/x-www-form-urlencoded'].schema.anyOf.length, 2);
  const invalid = transport('GET', 'plain'); invalid.variants[0].parameter_location = 'form-body';
  assert.throws(() => applyRequestTransports({'/example/': {get: operation()}}, [invalid], normalize), /Invalid transport/);
});

test('message rules distinguish client-required item fields from server-required fields', () => {
  const common = {'x-parser-method': 'LX/01pP;->unsafeParseFromJson', properties: {message: {}, _messages: {}}};
  const components = {schemas: {Common: common}};
  applySharedModels(components, {source_apk_sha256: 'synthetic', rules: {}}, 'synthetic');
  assert.deepEqual(components.schemas.ClientSystemMessage.required, ['key', 'time']);
  assert.equal(components.schemas.ClientSystemMessage['x-requiredness-scope'], 'client-parser');
  assert.equal(common.required, undefined);
  assert.equal(components.schemas.ClientMessageBranches.oneOf.length, 3);
  assert.equal(common.properties.message.$ref, '#/components/schemas/ClientMessageBranches');
  assert.throws(() => applySharedModels({schemas: {}}, {source_apk_sha256: 'other'}, 'synthetic'), /differs/);
});

test('403 uses the common parser while other error ranges retain their configured parser', () => {
  const op = operation(), components = {schemas: {}};
  const parser = name => ({method: name, recognized_fields: [{name: 'synthetic', evidence: [{}]}]});
  const contracts = {source_apk_sha256: 'synthetic', operations: [{path: '/example/', method: 'GET', parsers: [{type: 'LOrdinary;'}]}],
    error_operations: [{path: '/example/', method: 'GET', parsers: [{type: 'LError;'}]}],
    parsers: {'LOrdinary;': parser('ordinary'), 'LError;': parser('error'), 'LX/01pP;': parser('common')}};
  applyResponseModels({'/example/': {get: op}}, components, contracts, normalize, 'synthetic');
  assert.notDeepEqual(op.responses['403'].content, op.responses['4XX'].content);
  assert.notDeepEqual(op.responses.default.content, op.responses['4XX'].content);
  assert.equal(op.responses['4XX']['x-contract-scope'], 'client-error-dispatch');
  assert.match(op.responses['403'].description, /availability remain unverified/);
});

test('HTTP 200 anonymous failure is not counted as live success or a complete contract', () => {
  const op = operation();
  op['x-anonymous-response-observations'] = [{httpStatus: 200, instagramStatus: 'fail'}];
  const readiness = operationReadiness(op);
  assert.equal(readiness.live, 'not-tested');
  assert.equal(readiness.contract, 'partial');
  op.responses['4XX'] = {content: {'application/json': {schema: {type: 'object'}}}};
  assert.equal(operationReadiness(op).response, 'unresolved');
});
