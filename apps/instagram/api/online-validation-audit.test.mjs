import test from 'node:test';
import assert from 'node:assert/strict';
import {onlineValidationAudit} from './online-validation-audit.mjs';
test('audit accounts for success, failure and every class of skipped operation',()=>{
 const success={httpStatus:200,checkedOn:'fixture-date'};
 const audit=onlineValidationAudit({'/safe/':{get:{'x-live-check':success}},'/failed/':{get:{'x-read-validation':{httpStatus:400}}},'/unknown/':{get:{}},'/accounts/delete_music/':{get:{'x-live-check':success}},'/write/':{post:{}}});
 assert.equal(audit.operations.length,5);
 assert.deepEqual(audit.summary,{documentedOperations:5,observedSuccessfulReads:1,testedNotVerified:1,skippedWriteCapable:1,skippedSideEffectOrSecurityRisk:1,skippedUnreviewedReads:1});
 assert.equal(audit.operations.find(op=>op.path==='/safe/').successCheckedAt,'fixture-date');
 assert.equal(audit.operations.find(op=>op.path==='/accounts/delete_music/').state,'skipped-side-effect-or-security-risk');
});
