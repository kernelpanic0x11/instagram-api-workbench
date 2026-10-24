// A bounded contract for one pinned client construction and observed response.
// Server validation outside this profile remains open.
export const COMMENT_KEYWORDS_PATH = '/accounts/get_comment_filter_keywords/';
export function applyKeywordFilterContract(paths, components, evidence, observation, apkHash, endpoint = 'comment') {
  if (!['comment', 'post'].includes(endpoint)) throw new Error('Unsupported keyword endpoint');
  const route = '/accounts/get_' + endpoint + '_filter_keywords/';
  const modelPrefix = endpoint === 'comment' ? 'CommentKeywords' : 'PostKeywords';
  if (!evidence?.methods || !Object.keys(evidence.methods).length) return;
  if (evidence.source_apk_sha256 !== apkHash) throw new Error('Keyword contract APK provenance mismatch');
  const op = paths[route]?.get;
  if (!op) throw new Error('Keyword contract operation missing');
  const requiredMethods = [
    ...(endpoint === 'comment' ? ['LX/09eD;->A00(Lcom/instagram/common/session/UserSession;LX/09eD;LX/0Pmx;)Ljava/lang/Object;'] : [
      'LX/0HVZ;->onViewCreated(Landroid/view/View;Landroid/os/Bundle;)V',
      'LX/0Qvj;->Cya(ZLX/0Pmx;)Ljava/lang/Object;',
      'LX/0221;->A0K(LX/02rr;LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;']),
    'LX/0djX;->unsafeParseFromJson(LX/04s3;)Ljava/lang/Object;',
    'LX/01yt;->A0B(LX/04s3;)Ljava/util/ArrayList;',
    'LX/01yt;->A07(LX/04s3;)Ljava/lang/String;',
    'LX/0025;->A0H(LX/04s3;)Ljava/lang/Integer;'];
  if (requiredMethods.some(name => !evidence.methods[name])) throw new Error('Keyword parser evidence incomplete');
  components.schemas[modelPrefix + 'ClientObject'] = {
    type: 'object', additionalProperties: true, required: ['keywords'],
    description: 'Client acceptance model for an object consumed by 0djX. Missing/non-array keywords throws; an empty array is accepted. This required list is a client rule, not exhaustive server validation.',
    'x-requiredness-scope': 'client-parser',
    properties: {
      keywords: {type: 'array', items: {}, description: 'Array items pass through a String-coercing reader; decoded null items are dropped. Wire item types are not closed.', 'x-decoded-item-type': 'string'},
      disabled: {description: 'Optional; client uses integer reader A1b and boxes the result. Omission leaves the decoded field null. Coercion and wire nullability are not inferred.', 'x-decoded-type': 'integer'},
    },
  };
  op.parameters = [];
  delete op.requestBody;
  op['x-request-contract'] = {scope: 'pinned-client-construction', endpointParameters: [], body: 'none', encoding: 'plain query', signedBody: false,
    authentication: 'Verified Android session via the local proxy. Exact minimum header/cookie requirements not established.',
    completeness: 'Factory-to-finalization path adds no endpoint parameters; shared session/transport context remains applicable.'};
  op['x-client-response-model'] = {$ref: '#/components/schemas/' + modelPrefix + 'ClientObject'};
  op['x-focused-contract'] = {status: 'client-profile-traced', evidence: 'bulk-trace/' + endpoint + '-keywords-evidence.json',
    remaining: ['Nonempty keyword wire item types', 'Disabled wire variants and semantics', 'Minimum authentication headers', 'Conditional server validation and exhaustive errors', 'Alternate Pando/native response path']};
  op.description = 'Read the connected account’s ' + endpoint + '-filter keywords. The pinned Android caller configures GET, adds no endpoint parameters or body, finalizes a plain query request, and invokes its coroutine dispatcher. The JSON parser requires an array-valued keywords field (empty accepted), drops decoded null items, and optionally reads disabled through an integer reader. Additional common response fields are allowed. These are client rules; wire variants and exhaustive server errors remain open.';
  if (observation) {
    if (observation.path !== route || observation.method !== 'get' || observation.httpStatus !== 200 || observation.instagramStatus !== 'ok' || observation.rawResponseSaved !== false || observation.personalValuesSaved !== false) throw new Error('Invalid keyword success observation');
    components.schemas[modelPrefix + 'ObservedSuccess'] = {
      type: 'object', additionalProperties: true,
      description: 'Observed success profile, not a universal server schema. Field presence/types were checked without retaining values. An empty array provides no evidence of item wire types.',
      'x-contract-scope': 'observed-success-profile',
      properties: {status: {type: 'string', const: 'ok'}, keywords: {type: 'array', items: {}}, disabled: {type: 'integer'}},
    };
    op.responses['200'] = {description: 'Observed application/json success. HTTP 200 is not sufficient to establish application success; inspect status. Failure profiles remain partial.', content: {'application/json': {schema: {anyOf: [
      {$ref: '#/components/schemas/' + modelPrefix + 'ObservedSuccess'},
      {type: 'object', additionalProperties: true, required: ['status'], properties: {status: {const: 'fail'}, message: {type: 'string'}}},
    ]}}}};
    op['x-success-shape-observation'] = observation;
  }
  // The default and 4XX/5XX parser models remain available for unknown variants.
}
