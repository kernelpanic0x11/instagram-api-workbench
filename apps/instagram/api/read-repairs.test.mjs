import test from 'node:test';
import assert from 'node:assert/strict';
import {applyReadRepairs} from './read-repairs.mjs';
import {applyReadValidation} from './read-validation.mjs';
const entry={path:'/example/',method:'get',caller:'fixture',fields:[{name:'content_type',client_presence:'nonempty',encoding:'String'}],finding:'Partial review'};
const contracts={source_apk_sha256:'fixture',operations:[entry]},evidence={source_apk_sha256:'fixture',methods:{fixture:{}},reviewed_routes:['/example/']};
test('reviewed client parameter presence does not assert server requiredness',()=>{
 const paths={'/example/':{get:{description:'Partial',parameters:[]}}};
 applyReadRepairs(paths,contracts,evidence,'fixture');
 const parameter=paths['/example/'].get.parameters[0];
 assert.equal(parameter.name,'content_type');assert.equal(parameter.required,false);assert.equal(parameter['x-requiredness-status'],'unknown');
 assert.throws(()=>applyReadRepairs(paths,contracts,evidence,'other'),/provenance/);
 assert.throws(()=>applyReadRepairs(paths,contracts,{...evidence,methods:{}},'fixture'),/evidence/);
});
test('original failure and corrected attempt are both retained without a false success',()=>{
 const op={description:'Partial',responses:{default:{description:'Unknown'}}}, paths={'/example/':{get:op}};
 const check={path:'/example/',method:'get',httpStatus:400,outcome:'not-verified',rawResponseSaved:false,personalValuesSaved:false};
 for(const queryKeys of [[],['content_type']])applyReadValidation(paths,{schemas:{}},{source_apk_sha256:'fixture',checks:[{...check,queryKeys}]},'fixture');
 assert.equal(op['x-read-validation-history'].length,2);assert.equal(op['x-live-check'],undefined);
 assert.deepEqual(op['x-read-validation-history'][0].queryKeys,[]);
});
