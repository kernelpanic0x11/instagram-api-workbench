const EMPTY_SIGNED_BODY = 'SIGNATURE.{}';
const GET_FACTORY = 'LX/0221;->A0K(LX/02rr;LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;';
const SIGNED_ROUTE_FINALIZER = 'LX/0224;->A0P(LX/04x5;Ljava/lang/String;)LX/02sG;';
const REVIEWED_INPUT_DESCRIPTION = 'Reviewed bounded test input; server defaults and requiredness remain unproven.';

function reject(reason) {
  throw new Error('Reviewed read plan: ' + reason);
}

function methodProof(evidence, selector) {
  const proof = evidence.methods?.[selector];
  if (!proof || proof.method !== selector || !Array.isArray(proof.instructions) || !proof.instructions.length) reject('missing method proof');
  return proof;
}

function validateCallSite(caller, site, selector) {
  if (!site || site.selector !== selector || !Number.isInteger(site.codeUnitOffset) || site.codeUnitOffset < 0 ||
      !Number.isInteger(site.dexByteOffset) || site.dexByteOffset !== caller.code_item_byte_offset + 16 + 2 * site.codeUnitOffset) reject('invalid call offset or selector');
  const matching = caller.instructions.filter(instruction => instruction.code_unit_offset === site.codeUnitOffset);
  if (matching.length !== 1 || matching[0].callee !== selector || matching[0].dex_byte_offset !== site.dexByteOffset) reject('call site differs from pinned instruction proof');
}

function publicCallSite(site) {
  return {selector: site.selector, codeUnitOffset: site.codeUnitOffset, dexByteOffset: site.dexByteOffset};
}

function matchingFinalization(variant, review) {
  return variant.status === 'client-finalization-traced' && variant.parameter_location === 'query' && variant.envelope === 'signed' &&
    variant.evidence?.some(record => record.operation === 'request-finalization' && record.caller === review.caller &&
      record.dex === review.dex && record.method_index === review.callerMethodIndex &&
      record.callee === review.routeFinalizer.selector && record.code_unit_offset === review.routeFinalizer.codeUnitOffset &&
      record.dex_byte_offset === review.routeFinalizer.dexByteOffset);
}

// Review authorizes only the recorded empty query envelope. It does not imply
// server acceptance, account eligibility, universal requiredness or a live test.
export function applyReviewedReadPlan(paths, plan, evidence, apkSha) {
  if (!Array.isArray(plan?.targets)) reject('missing target list');
  const targets = plan.targets.filter(target => Object.hasOwn(target, 'staticReview'));
  if (!targets.length) return;
  if (plan.source_apk_sha256 !== apkSha || evidence?.source_apk_sha256 !== apkSha) reject('APK provenance mismatch');
  const prepared = [], seen = new Set();
  for (const target of targets) {
    const review = target.staticReview;
    const operation = paths[target.path]?.get;
    if (!review || typeof review !== 'object' || target.method !== 'get' || !operation || seen.has(target.path) ||
        !evidence.reviewed_routes?.includes(target.path)) reject('unknown, duplicate or unreviewed GET route');
    seen.add(target.path);
    if (!target.query || Object.keys(target.query).length !== 1 || target.query.signed_body !== EMPTY_SIGNED_BODY ||
        !Array.isArray(review.endpointParameterKeys) || review.endpointParameterKeys.length) reject('incorrect empty signed payload');
    if (review.evidence !== 'bulk-trace/reviewed-read-evidence.json' || review.sharedFinalizationEvidence !== 'bulk-trace/shared-contracts.json' ||
        review.sharedFinalizer !== 'LX/04x6;->A02()LX/02uC;') reject('unexpected evidence reference');
    const caller = methodProof(evidence, review.caller);
    if (caller.dex !== review.dex || caller.method_index !== review.callerMethodIndex) reject('caller provenance mismatch');
    validateCallSite(caller, review.factory, GET_FACTORY);
    validateCallSite(caller, review.routeFinalizer, SIGNED_ROUTE_FINALIZER);
    if (review.factory.codeUnitOffset >= review.routeFinalizer.codeUnitOffset || !caller.instructions.some(instruction =>
      instruction.code_unit_offset > review.factory.codeUnitOffset && instruction.code_unit_offset < review.routeFinalizer.codeUnitOffset &&
      instruction.string === target.path.replace(/^\//, ''))) reject('route literal is not bound to this construction');
    methodProof(evidence, GET_FACTORY);
    methodProof(evidence, SIGNED_ROUTE_FINALIZER);
    methodProof(evidence, review.parser);
    const callback = methodProof(evidence, review.callback);
    const parserOwner = review.parser.split('->')[0], callbackOwner = review.callback.split('->')[0];
    if (!caller.instructions.some(instruction => instruction.code_unit_offset < review.factory.codeUnitOffset && instruction.field === parserOwner + '->A00' + parserOwner) ||
        !caller.instructions.some(instruction => instruction.code_unit_offset > review.routeFinalizer.codeUnitOffset && instruction.callee?.startsWith(callbackOwner + '-><init>('))) reject('parser or callback differs from caller construction');
    if (review.callbackContext?.branchCodeUnitOffset !== undefined && !callback.instructions.some(instruction => instruction.code_unit_offset === review.callbackContext.branchCodeUnitOffset)) reject('callback branch lacks instruction proof');
    if (review.callbackContext?.followupSelector) methodProof(evidence, review.callbackContext.followupSelector);
    if (!operation['x-request-transport']?.some(variant => matchingFinalization(variant, review))) reject('missing matching finalized signed-query variant');
    const parameters = (operation.parameters ?? []).filter(parameter => parameter.in === 'query' && parameter.name === 'signed_body');
    if (parameters.length !== 1 || parameters[0].schema?.type !== 'string' || parameters[0].required === true) reject('missing or conflicting signed_body query parameter');
    prepared.push({target, review, operation, parameter: parameters[0]});
  }
  // Validate every target before changing any operation, so stale evidence
  // cannot leave a partly applied review behind.
  for (const {target, review, operation, parameter} of prepared) {
    operation['x-reviewed-read-plan'] = {
      status: 'static-input-reviewed',
      scope: 'One bounded input reviewed against the pinned client. Live success is recorded separately.',
      sourceApkSha256: apkSha, path: target.path, method: 'get', query: {signed_body: EMPTY_SIGNED_BODY},
      evidence: review.evidence, sharedFinalizationEvidence: review.sharedFinalizationEvidence,
      caller: review.caller, dex: review.dex, callerMethodIndex: review.callerMethodIndex,
      factory: publicCallSite(review.factory), routeFinalizer: publicCallSite(review.routeFinalizer),
      endpointParameterKeys: [], sharedFinalizer: review.sharedFinalizer,
      parser: review.parser, callback: review.callback,
      callbackContext: {
        ...(review.callbackContext?.discriminator !== undefined ? {discriminator: review.callbackContext.discriminator} : {}),
        ...(review.callbackContext?.branchCodeUnitOffset !== undefined ? {branchCodeUnitOffset: review.callbackContext.branchCodeUnitOffset} : {}),
        ...(review.callbackContext?.followupSelector ? {followupSelector: review.callbackContext.followupSelector} : {}),
      },
      construction: review.construction, readOnlyRationale: review.readOnlyRationale, limitations: review.limitations,
    };
    parameter.example = EMPTY_SIGNED_BODY;
    parameter['x-requiredness-status'] = 'unknown';
    if (!parameter.description?.includes(REVIEWED_INPUT_DESCRIPTION)) parameter.description = [parameter.description, REVIEWED_INPUT_DESCRIPTION].filter(Boolean).join(' ');
  }
}
