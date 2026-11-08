import test from 'node:test';
import assert from 'node:assert/strict';
import {applyReadValidation} from './read-validation.mjs';
const check={path:'/example/',method:'get',httpStatus:200,contentType:'application/json',instagramStatus:'ok',bodyKind:'object',outcome:'observed-success',fieldTypes:{status:'string',items:'array'},arrayItemTypes:{items:[]},rawResponseSaved:false,personalValuesSaved:false};
function apply(c=check,hash='fixture'){
 const paths={'/example/':{get:{operationId:'example',responses:{default:{description:'partial'}},'x-recovered-response-fields':[{name:'items'}]}}}, components={schemas:{}};
 applyReadValidation(paths,components,{source_apk_sha256:'fixture',checks:[c]},hash);return {op:paths['/example/'].get,components};
}
test('observed types remain open and application failures are distinguished',()=>{
 const {op,components}=apply();assert.ok(op['x-live-check']);assert.ok(op.responses.default);
 const schema=components.schemas.ObservedRead_example;
 assert.equal(schema.required,undefined);assert.equal(schema.additionalProperties,true);
 assert.deepEqual(schema.properties.items.items,{});
 assert.deepEqual(schema.properties.items['x-observed-item-types'],[]);
 const failed=apply({...check,outcome:'not-verified',instagramStatus:'fail'});
 assert.equal(failed.op['x-live-check'],undefined);assert.equal(failed.op.responses['200']['x-contract-scope'],'observed-unsuccessful-read');
});
test('metadata rejects mismatched provenance, unknown fields and false success',()=>{
 assert.throws(()=>apply(check,'other'),/provenance/);
 assert.throws(()=>apply({...check,fieldTypes:{private_key:'string'}}),/metadata/);
 assert.throws(()=>apply({...check,instagramStatus:'fail'}),/successful/);
 assert.throws(()=>apply({...check,personalValuesSaved:true}),/observation/);
});
test('stronger curated 200 response remains intact',()=>{
 const response={description:'curated'};const paths={'/example/':{get:{operationId:'example',responses:{200:response},'x-recovered-response-fields':[{name:'items'}]}}};
 applyReadValidation(paths,{schemas:{}},{source_apk_sha256:'fixture',checks:[check]},'fixture');
 assert.equal(paths['/example/'].get.responses['200'],response);
});

test('a later successful transport read replaces an observed-failure 200 description and retains history',()=>{
 const paths={'/example/':{get:{operationId:'example',description:'Partial',responses:{default:{description:'Unknown'}},'x-recovered-response-fields':[{name:'items'}]}}},components={schemas:{}};
 applyReadValidation(paths,components,{source_apk_sha256:'fixture',checks:[{...check,outcome:'not-verified',instagramStatus:'fail'}]},'fixture');
 assert.equal(paths['/example/'].get.responses['200']['x-contract-scope'],'observed-unsuccessful-read');
 applyReadValidation(paths,components,{source_apk_sha256:'fixture',checks:[check]},'fixture');
 assert.ok(paths['/example/'].get.responses['200'].content['application/json']);
 assert.equal(paths['/example/'].get['x-read-validation-history'].length,2);
 assert.equal(paths['/example/'].get['x-live-check'].instagramStatus,'ok');
});

function applySequence(checks, initialLiveCheck) {
 const paths={'/example/':{get:{operationId:'example',description:'Partial',responses:{default:{description:'Unknown'}},'x-recovered-response-fields':[{name:'items'}],...(initialLiveCheck?{'x-live-check':initialLiveCheck}:{})}}};
 const components={schemas:{}};
 for(const observation of checks) applyReadValidation(paths,components,{source_apk_sha256:'fixture',checks:[observation]},'fixture');
 return {op:paths['/example/'].get,components};
}
const datedSuccess={...check,checkedAt:'2026-10-24T02:00:00Z'};
const olderFailure={...check,checkedAt:'2026-10-23T02:00:00Z',outcome:'not-verified',instagramStatus:'fail',httpStatus:400};

test('older failure loaded after a newer success cannot become the latest attempt',()=>{
 for(const observations of [[olderFailure,datedSuccess],[datedSuccess,olderFailure]]){
  const {op,components}=applySequence(observations);
  assert.equal(op['x-read-validation'].checkedAt,datedSuccess.checkedAt);
  assert.equal(op['x-read-validation'].outcome,'observed-success');
  assert.equal(op['x-live-check'].checkedAt,datedSuccess.checkedAt);
  assert.deepEqual(components.schemas.ObservedRead_example.properties.items['x-observed-item-types'],[]);
  assert.equal(op['x-read-validation-history'].length,2);
  assert.equal(op.responses['400']['x-contract-scope'],'observed-unsuccessful-read');
 }
});

test('success schema follows the newest successful observation in either artifact order',()=>{
 const older={...datedSuccess,checkedAt:'2026-10-22T02:00:00Z',fieldTypes:{status:'string',items:'array'},arrayItemTypes:{items:['string']}};
 const newer={...datedSuccess,fieldTypes:{status:'string',items:'object'},arrayItemTypes:{}};
 for(const observations of [[older,newer],[newer,older]]){
  const {op,components}=applySequence(observations);
  assert.equal(op['x-read-validation'].checkedAt,newer.checkedAt);
  assert.equal(op['x-live-check'].checkedAt,newer.checkedAt);
  assert.deepEqual(components.schemas.ObservedRead_example.properties.items,{type:'object'});
  assert.equal(op['x-observed-success-model'].$ref,'#/components/schemas/ObservedRead_example');
 }
});

test('newer failure remains latest while an older success supplies historical evidence',()=>{
 const newerFailure={...olderFailure,checkedAt:'2026-10-25T02:00:00Z'};
 for(const observations of [[datedSuccess,newerFailure],[newerFailure,datedSuccess]]){
  const {op,components}=applySequence(observations);
  assert.equal(op['x-read-validation'].checkedAt,newerFailure.checkedAt);
  assert.equal(op['x-read-validation'].outcome,'not-verified');
  assert.equal(op['x-live-check'].checkedAt,datedSuccess.checkedAt);
  assert.equal(components.schemas.ObservedRead_example.properties.items.type,'array');
  assert.ok(op.responses['200'].content['application/json']);
 }
});

test('legacy checkedOn success is considered when selecting the latest attempt',()=>{
 const legacy={httpStatus:200,instagramStatus:'ok',checkedOn:'2026-10-24'};
 const {op}=applySequence([olderFailure],legacy);
 assert.equal(op['x-read-validation'].checkedOn,'2026-10-24');
 assert.equal(op['x-live-check'].checkedOn,'2026-10-24');
 assert.equal(op['x-read-validation-history'][0].outcome,'not-verified');
 const nextDay={...olderFailure,checkedAt:undefined,checkedOn:'2026-10-25'};
 const later=applySequence([nextDay],legacy);
 assert.equal(later.op['x-read-validation'].checkedOn,'2026-10-25');
 assert.equal(later.op['x-live-check'].checkedOn,'2026-10-24');
});

test('timestamp comparison uses offsets rather than date string ordering',()=>{
 const newer={...datedSuccess,checkedAt:'2026-10-23T20:00:00-06:00',fieldTypes:{status:'string',items:'object'}};
 const older={...datedSuccess,checkedAt:'2026-10-24T02:00:00+02:00'};
 for(const observations of [[older,newer],[newer,older]]){
  const {op,components}=applySequence(observations);
  assert.equal(op['x-live-check'].checkedAt,newer.checkedAt);
  assert.equal(components.schemas.ObservedRead_example.properties.items.type,'object');
 }
});

test('undated and malformed observations cannot replace dated records or their success models',()=>{
 for(const timestamp of [undefined,'invalid-date','2026-02-30T23:59:00Z','2026-10-25T02:00:00']){
  const undated={...check,checkedAt:timestamp,fieldTypes:{status:'string',items:'object'}};
  const {op,components}=applySequence([datedSuccess,undated]);
  assert.equal(op['x-read-validation'].checkedAt,datedSuccess.checkedAt);
  assert.equal(op['x-live-check'].checkedAt,datedSuccess.checkedAt);
  assert.equal(components.schemas.ObservedRead_example.properties.items.type,'array');
  assert.equal(op['x-read-validation-history'].length,2);
 }
});

test('valid checkedOn is a fallback for malformed checkedAt',()=>{
 const newer={...check,checkedAt:'invalid-date',checkedOn:'2026-10-25',fieldTypes:{status:'string',items:'object'}};
 const {op,components}=applySequence([datedSuccess,newer]);
 assert.equal(op['x-read-validation'].checkedOn,'2026-10-25');
 assert.equal(op['x-live-check'].checkedOn,'2026-10-25');
 assert.equal(components.schemas.ObservedRead_example.properties.items.type,'object');
});

test('legacy undated pairs retain explicit last-loaded-wins behavior',()=>{
 const first={...check,fieldTypes:{status:'string',items:'array'}};
 const second={...check,fieldTypes:{status:'string',items:'object'}};
 const {op,components}=applySequence([first,second]);
 assert.deepEqual(op['x-read-validation'].fieldTypes,second.fieldTypes);
 assert.deepEqual(op['x-live-check'].fieldTypes,second.fieldTypes);
 assert.equal(components.schemas.ObservedRead_example.properties.items.type,'object');
 const failed={...check,outcome:'not-verified',instagramStatus:'fail'};
 const result=applySequence([first,failed]);
 assert.equal(result.op['x-read-validation'].outcome,'not-verified');
 assert.equal(result.op['x-live-check'].outcome,'observed-success');
});

test('equal timestamps preserve the existing profile instead of inferring recency from load order',()=>{
 const conflicting={...datedSuccess,fieldTypes:{status:'string',items:'object'}};
 const {op,components}=applySequence([datedSuccess,conflicting]);
 assert.deepEqual(op['x-live-check'].fieldTypes,datedSuccess.fieldTypes);
 assert.equal(components.schemas.ObservedRead_example.properties.items.type,'array');
 assert.equal(op['x-read-validation-history'].length,2);
});

test('precise same-day checkedAt takes precedence over a legacy checkedOn date',()=>{
 const coarse={...check,checkedOn:'2026-10-24',fieldTypes:{status:'string',items:'object'}};
 for(const observations of [[coarse,datedSuccess],[datedSuccess,coarse]]){
  const {op,components}=applySequence(observations);
  assert.equal(op['x-read-validation'].checkedAt,datedSuccess.checkedAt);
  assert.equal(op['x-live-check'].checkedAt,datedSuccess.checkedAt);
  assert.equal(components.schemas.ObservedRead_example.properties.items.type,'array');
 }
});

test('an older false-success record is still rejected before mutating current evidence',()=>{
 const {op,components}=applySequence([datedSuccess]);
 const paths={'/example/':{get:op}}, before=structuredClone({paths,components});
 const invalidOlder={...olderFailure,outcome:'observed-success'};
 assert.throws(()=>applyReadValidation(paths,components,{source_apk_sha256:'fixture',checks:[invalidOlder]},'fixture'),/Invalid successful read/);
 assert.deepEqual({paths,components},before);
});
