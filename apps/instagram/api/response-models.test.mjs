import test from 'node:test';
import assert from 'node:assert/strict';
import {applyResponseModels} from './response-models.mjs';

const normalize = path => ({path});
const fixture = () => ({source_apk_sha256: 'synthetic', operations: [{path: '/example/', method: 'GET', parsers: [{type: 'LParser;', evidence: {dex_byte_offset: 10}}]}],
  parsers: {'LParser;': {method: 'LParser;->unsafeParseFromJson', dex_sha256: 'synthetic-dex', recognized_fields: [{name: 'example', evidence: [{dex_byte_offset: 20}]}]}}});

test('parser keys create permissive partial schemas without invented types or requiredness', () => {
  const operation = {description: 'Synthetic', responses: {default: {description: 'Unknown'}}};
  const components = {schemas: {}};
  applyResponseModels({'/example/': {get: operation}}, components, fixture(), normalize, 'synthetic');
  const model = Object.values(components.schemas)[0];
  assert.equal(model.additionalProperties, true);
  assert.equal(model.properties.example.type, undefined);
  assert.equal(model.required, undefined);
  assert.ok(operation.responses.default.content['application/json']);
  assert.match(operation.responses.default['x-media-type-status'], /unverified/);
  assert.deepEqual(Object.keys(operation.responses), ['default']);
});

test('a stronger manually traced response model is preserved', () => {
  const original = {schema: {$ref: '#/components/schemas/ManuallyTraced'}};
  const operation = {description: 'Synthetic', responses: {default: {content: {'application/json': original}}}};
  applyResponseModels({'/example/': {get: operation}}, {schemas: {}}, fixture(), normalize, 'synthetic');
  assert.equal(operation.responses.default.content['application/json'], original);
  assert.ok(operation['x-response-models'].length);
});

test('mismatched input provenance cannot attach response models', () => {
  assert.throws(() => applyResponseModels({}, {schemas: {}}, fixture(), normalize, 'other-input'), /differs/);
});

test('normalized route variants retain every observed parser model', () => {
  const contracts = fixture();
  contracts.parsers['LOtherParser;'] = {...contracts.parsers['LParser;'], recognized_fields: [{name: 'other', evidence: [{dex_byte_offset: 30}]}]};
  contracts.operations.push({path: '/example/?variant=1', method: 'GET', parsers: [{type: 'LOtherParser;'}]});
  const operation = {description: 'Synthetic', responses: {default: {description: 'Unknown'}}};
  applyResponseModels({'/example/': {get: operation}}, {schemas: {}}, contracts, path => ({path: path.split('?')[0]}), 'synthetic');
  assert.equal(operation['x-response-models'].length, 2);
  assert.equal(operation.responses.default.content['application/json'].schema.anyOf.length, 2);
  assert.deepEqual(operation['x-recovered-response-fields'].map(field => field.name), ['example', 'other']);
});

test('client reader signatures and nullable child parsers remain separate from wire constraints',()=>{
 const contracts=fixture();
 contracts.parsers['LParser;'].recognized_fields[0].client_reader_calls=[{callee:'LHelper;->read',return_descriptor:'LChild;',nested_parser:'LChildParser;'}];
 contracts.parsers['LChildParser;']={method:'LChildParser;->unsafeParseFromJson',dex_sha256:'synthetic',recognized_fields:[{name:'child_key',evidence:[]}]};
 const op={description:'Synthetic',responses:{default:{description:'Unknown'}}},components={schemas:{}};
 applyResponseModels({'/example/':{get:op}},components,contracts,normalize,'synthetic');
 const root=components.schemas[op['x-response-models'][0].$ref.split('/').at(-1)];
 assert.equal(root.properties.example.type,undefined);assert.equal(root.properties.example.required,undefined);
 assert.equal(root.properties.example['x-client-reader-calls'][0].return_descriptor,'LChild;');
 const child=root.properties.example['x-client-nested-response-models'][0];
 assert.ok(components.schemas[child.$ref.split('/').at(-1)].properties.child_key);
 assert.equal(op['x-recovered-response-fields'][0].client_reader_calls.length,1);
});
