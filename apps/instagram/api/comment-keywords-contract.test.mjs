import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {applyKeywordFilterContract,COMMENT_KEYWORDS_PATH as path} from './comment-keywords-contract.mjs';
const read = name => JSON.parse(fs.readFileSync(new URL(name,import.meta.url)));
const evidence=read('bulk-trace/comment-keywords-evidence.json');
const observation=read('comment-keywords-observation.json');
function apply(e=evidence,o=observation,hash=evidence.source_apk_sha256){
 const paths={[path]:{get:{description:'partial',responses:{default:{description:'unknown'},'4XX':{description:'client error'}}}}},components={schemas:{}};
 applyKeywordFilterContract(paths,components,e,o,hash);return {op:paths[path].get,components};
}
test('keyword contract separates client requirements, observed wire types and unknown variants',()=>{
 const {op,components}=apply();
 assert.deepEqual(op.parameters,[]);assert.equal(op.requestBody,undefined);
 assert.equal(op['x-request-contract'].signedBody,false);
 assert.deepEqual(components.schemas.CommentKeywordsClientObject.required,['keywords']);
 assert.equal(components.schemas.CommentKeywordsClientObject.properties.disabled.type,undefined);
 assert.deepEqual(components.schemas.CommentKeywordsObservedSuccess.properties.keywords.items,{});
 assert.equal(components.schemas.CommentKeywordsObservedSuccess.required,undefined);
 assert.equal(op.responses['200'].content['application/json'].schema.anyOf[1].properties.status.const,'fail');
 assert.ok(op.responses.default);assert.ok(op.responses['4XX']);
});
test('keyword contract requires matching provenance and sanitized observations',()=>{
 assert.throws(()=>apply(evidence,observation,'different'),/provenance/);
 assert.equal(apply({...evidence,methods:{}},observation,'different').op['x-focused-contract'],undefined);
 const incomplete={...evidence,methods:{}};incomplete.methods[Object.keys(evidence.methods)[0]]=Object.values(evidence.methods)[0];
 assert.throws(()=>apply(incomplete),/incomplete/);
});
test('offline reproductions can attach static rules without copying live observations',()=>{
 const {op,components}=apply(evidence,null);
 assert.ok(op['x-client-response-model']);assert.equal(op.responses['200'],undefined);
 assert.equal(components.schemas.CommentKeywordsObservedSuccess,undefined);
 assert.throws(()=>apply(evidence,{...observation,personalValuesSaved:true}),/observation/);
});

test('post contract uses its own route, caller evidence and response models',()=>{
 const postEvidence=read('bulk-trace/post-keywords-evidence.json');
 const postObservation={...observation,path:'/accounts/get_post_filter_keywords/'};
 const paths={[postObservation.path]:{get:{responses:{default:{description:'unknown'}}}}},components={schemas:{}};
 applyKeywordFilterContract(paths,components,postEvidence,postObservation,postEvidence.source_apk_sha256,'post');
 assert.ok(components.schemas.PostKeywordsClientObject);
 assert.equal(components.schemas.CommentKeywordsClientObject,undefined);
 assert.equal(paths[postObservation.path].get['x-request-contract'].signedBody,false);
 assert.match(paths[postObservation.path].get['x-focused-contract'].evidence,/post-keywords/);
 assert.throws(()=>applyKeywordFilterContract(paths,components,postEvidence,observation,postEvidence.source_apk_sha256,'post'),/observation/);
 assert.throws(()=>applyKeywordFilterContract(paths,components,evidence,null,evidence.source_apk_sha256,'post'),/incomplete/);
});
