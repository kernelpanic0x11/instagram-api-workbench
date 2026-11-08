import test from 'node:test';
import assert from 'node:assert/strict';
import {applyContextReadRepairs,applyContextReadRepairExamples} from './context-read-repairs.mjs';
import {applyReadValidation} from './read-validation.mjs';

function fixture() {
  const operations = Array.from({length:37}, (_, index) => ({path:`/read/${index}/`, fields:{q:'Search string',user_id:'Current account'}}));
  const paths = Object.fromEntries(operations.map(entry => [entry.path, {get:{operationId:entry.path, responses:{},
    parameters:Object.keys(entry.fields).map(name => ({name,in:'query',required:false,schema:{type:'string'}}))}}]));
  return {paths, review:{source_apk_sha256:'apk',operations}, safety:{blockedRoutes:[]},
    plan:{source_apk_sha256:'apk',corrections:{'reviewed-search':{path:'/read/0/',
      query:{q:'public-term',user_id:{source:'verified-account-id'}},evidence:'Pinned caller and parameter evidence.'}}}};
}
function apply(f) { applyContextReadRepairs(f.paths,f.plan,f.review,f.safety,'apk'); }
const success = {path:'/read/0/',method:'get',correction:'reviewed-search',queryKeys:['q','user_id'],requestBodySent:false,
  outcome:'observed-success',httpStatus:200,instagramStatus:'ok',contentType:'application/json',bodyKind:'object',
  rawResponseSaved:false,personalValuesSaved:false,checkedAt:'2026-10-24T20:00:00Z',fieldTypes:{status:'string'}};

test('reviewed context descriptors remain metadata and do not become literal examples or live success', () => {
  const f=fixture();apply(f);const operation=f.paths['/read/0/'].get;
  assert.deepEqual(operation['x-context-read-repairs'][0].query.user_id,{source:'verified-account-id'});
  assert.match(operation['x-context-read-repairs'][0].note,/not literal query values/);
  assert.equal(operation['x-context-read-repairs'][0].purpose,'request-correction');
  assert.ok(operation.parameters.every(parameter => parameter.example === undefined));
  assert.equal(operation['x-live-check'],undefined);
});

test('provenance, complete frozen review, GET route, safety, fields and descriptor shape fail closed', () => {
  for (const mutate of [f=>f.plan.source_apk_sha256='other',f=>f.review.source_apk_sha256='other',
    f=>f.review.operations.pop(),f=>delete f.paths['/read/0/'].get,
    f=>f.safety.blockedRoutes.push('/read/0/'),f=>f.plan.corrections['reviewed-search'].query.unreviewed='value',
    f=>f.plan.corrections['reviewed-search'].query.user_id.value='private',
    f=>f.plan.corrections['reviewed-search'].query.user_id={source:'not a descriptor'},
    f=>f.plan.corrections['reviewed-search'].purpose='unreviewed']) {
    const f=fixture();mutate(f);const before=structuredClone(f.paths);
    assert.throws(()=>apply(f),/Context read repairs/);assert.deepEqual(f.paths,before);
  }
});

test('a later invalid correction cannot leave earlier metadata partly applied', () => {
  const f=fixture();f.plan.corrections['invalid-route']={path:'/unknown/',query:{},evidence:'Unbound'};
  const before=structuredClone(f.paths);assert.throws(()=>apply(f));assert.deepEqual(f.paths,before);
});

test('only matching observed success publishes public literals, leaving account descriptors unexecuted', () => {
  const f=fixture();apply(f);const results={source_apk_sha256:'apk',checks:[success]};
  applyReadValidation(f.paths,{schemas:{}},results,'apk');
  applyContextReadRepairExamples(f.paths,f.plan,results,'apk');
  const operation=f.paths['/read/0/'].get;
  assert.equal(operation.parameters.find(parameter=>parameter.name==='q').example,'public-term');
  assert.equal(operation.parameters.find(parameter=>parameter.name==='user_id').example,undefined);
  assert.deepEqual(operation['x-tested-context-query-literals'].values,{q:'public-term'});
});

test('failure, unselected historical success and diagnostic-only purpose do not publish examples', () => {
  for (const mode of ['failure','historical','diagnostic-only']) {
    const f=fixture();if(mode==='diagnostic-only')f.plan.corrections['reviewed-search'].purpose=mode;
    apply(f);const check=mode==='failure'?{...success,outcome:'not-verified',instagramStatus:'fail'}:success;
    const results={source_apk_sha256:'apk',checks:[check]};applyReadValidation(f.paths,{schemas:{}},results,'apk');
    if(mode==='historical')f.paths['/read/0/'].get['x-live-check']={...success,correction:'newer-construction'};
    applyContextReadRepairExamples(f.paths,f.plan,results,'apk');
    assert.ok(f.paths['/read/0/'].get.parameters.every(parameter=>parameter.example===undefined));
    if(mode==='diagnostic-only')assert.equal(f.paths['/read/0/'].get['x-context-read-repairs'][0].purpose,mode);
  }
});

test('unknown successful corrections and changed query keys cannot claim tested examples', () => {
  for (const change of [{correction:'unknown'},{queryKeys:['q']},{requestBodySent:true},{instagramStatus:'fail'}]) {
    const f=fixture();apply(f);const check={...success,...change};f.paths['/read/0/'].get['x-live-check']=check;
    assert.throws(()=>applyContextReadRepairExamples(f.paths,f.plan,{source_apk_sha256:'apk',checks:[check]},'apk'));
    assert.ok(f.paths['/read/0/'].get.parameters.every(parameter=>parameter.example===undefined));
  }
});
