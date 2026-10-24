import test from 'node:test';
import assert from 'node:assert/strict';
import {applyRemainingReadReview,remainingReadAudit} from './remaining-read-review.mjs';
const fixture=()=>{
 const operations=Array.from({length:37},(_,i)=>({path:`/read/${i}/`,priorHttpStatus:400,disposition:i===0?'corrected-read':'needs-context',fields:{q:'Caller string'},callers:[`caller-${i}`],finding:'Client construction only.'}));
 return {paths:Object.fromEntries(operations.map(o=>[o.path,{get:{description:'Read',responses:{default:{description:'Unknown'}}}}])),
   review:{source_apk_sha256:'apk',operations},evidence:{source_apk_sha256:'apk',reviewed_routes:operations.map(o=>o.path),methods:Object.fromEntries(operations.map(o=>[o.callers[0],{}]))}};
};
test('all 37 reviews attach unknown-requiredness parameters without claiming runtime success',()=>{
 const {paths,review,evidence}=fixture();applyRemainingReadReview(paths,review,evidence,'apk');
 assert.equal(Object.keys(paths).length,37);
 assert.equal(paths['/read/0/'].get.parameters[0].required,false);
 assert.equal(paths['/read/0/'].get.parameters[0]['x-requiredness-status'],'unknown');
 assert.equal(paths['/read/0/'].get['x-live-check'],undefined);
 assert.deepEqual(remainingReadAudit(paths,review).summary,{reviewed:37,correctedRequests:1,nowSuccessful:0,stillUnverified:37,deferred:36});
});
test('incomplete review, stale provenance and missing caller proof fail closed',()=>{
 for(const mutate of [f=>f.review.operations.pop(),f=>f.evidence.source_apk_sha256='other',f=>delete f.evidence.methods['caller-1']]){
  const f=fixture();mutate(f);assert.throws(()=>applyRemainingReadReview(f.paths,f.review,f.evidence,'apk'));
 }
});
test('audit uses live evidence rather than treating an HTTP 200 failure as success',()=>{
 const {paths,review,evidence}=fixture();applyRemainingReadReview(paths,review,evidence,'apk');
 paths['/read/0/'].get['x-read-validation']={httpStatus:200,instagramStatus:'fail'};
 paths['/read/1/'].get['x-live-check']={httpStatus:200,instagramStatus:'ok'};
 assert.equal(remainingReadAudit(paths,review).summary.nowSuccessful,1);
 assert.equal(remainingReadAudit(paths,review).operations[0].outcome,'not-verified');
});
