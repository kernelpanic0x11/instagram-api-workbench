import fs from 'node:fs';
import {HTTP_METHODS} from './operation-coverage.mjs';
const blocked = new Set(JSON.parse(fs.readFileSync(new URL('online-read-safety.json',import.meta.url))).blockedRoutes);
export function onlineValidationAudit(paths) {
  const operations=[];
  for(const [path,item] of Object.entries(paths))for(const method of HTTP_METHODS){
    const op=item[method];if(!op)continue;
    let state,reason;
    if(method!=='get'){state='skipped-write-capable';reason='Read-only scope: no writes, messages, deletions or other account changes authorized.';}
    else if(blocked.has(path)){state='skipped-side-effect-or-security-risk';reason='GET route may change state, start security recovery, or has ambiguous change semantics.';}
    else if(op['x-live-check']){state='observed-success';reason='One recorded HTTP-200 JSON status-ok read; not a complete contract or continuing guarantee.';}
    else if(op['x-read-validation']){state='tested-not-verified';reason='Recorded read did not meet the application-success check.';}
    else {state='skipped-unreviewed-read';reason='Request inputs or side effects not sufficiently reviewed; fixture/context may be needed.';}
    const check=op['x-read-validation']??op['x-live-check'];
    operations.push({path,method,state,reason,...(check?{httpStatus:check.httpStatus,checkedAt:check.checkedAt??check.checkedOn}:{}),...(op['x-live-check']?{successCheckedAt:op['x-live-check'].checkedAt??op['x-live-check'].checkedOn}: {})});
  }
  const count=state=>operations.filter(op=>op.state===state).length;
  return {scope:'Audit of every documented operation. Historical observations and this pass are not all fresh tests. Unknown-method candidates are not executable. No write-capable or explicitly blocked GET routes executed.',summary:{documentedOperations:operations.length,observedSuccessfulReads:count('observed-success'),testedNotVerified:count('tested-not-verified'),skippedWriteCapable:count('skipped-write-capable'),skippedSideEffectOrSecurityRisk:count('skipped-side-effect-or-security-risk'),skippedUnreviewedReads:count('skipped-unreviewed-read')},operations};
}
