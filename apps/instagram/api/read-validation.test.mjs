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
