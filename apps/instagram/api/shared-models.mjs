export function applySharedModels(components, shared, apkSha256) {
  if (shared.source_apk_sha256 !== apkSha256) throw new Error('Shared contract evidence differs from target APK');
  if (!shared.rules) return;
  components.schemas.ClientSystemMessage = {type: 'object', additionalProperties: true,
    description: 'Partial client acceptance model for an object consumed by the _messages item parser. The client throws if decoded key or time is absent. This does not establish that _messages is required or that the server guarantees these fields.',
    required: ['key', 'time'], 'x-requiredness-scope': 'client-parser',
    properties: {key: {'x-client-decoded-type': 'nonnull String', description: 'String-coercing reader; closed wire type not asserted.'},
                 time: {'x-client-decoded-type': 'float', description: 'Numeric reader followed by double-to-float conversion; accepted wire coercions unverified.'}},
    'x-evidence-method': 'LX/0Kbr;->unsafeParseFromJson(LX/04s3;)Ljava/lang/Object;'};
  components.schemas.ClientMessageBranches = {description: 'Observed common client handling of message by JSON token kind. All JSON kinds remain allowed; these branches describe consumption behavior, not a closed server contract.',
    oneOf: [{type: 'object', additionalProperties: true, properties: {errors: {description: 'Only the array branch is consumed. Decoded String items are collected; null decoded items throw. Other value types are skipped.', 'x-client-array-item-decoded-type': 'nonnull String'}}},
            {type: 'array', items: {}, 'x-client-behavior': 'skipped'},
            {type: ['string', 'number', 'boolean', 'null'], 'x-client-behavior': 'String-coercing reader'}],
    'x-evidence-method': 'LX/01y9;->A01(LX/04s3;)V'};
  for (const model of Object.values(components.schemas)) if (model['x-parser-method']?.startsWith('LX/01pP;')) {
    if (model.properties.message) model.properties.message = {...model.properties.message, $ref: '#/components/schemas/ClientMessageBranches'};
    if (model.properties._messages) model.properties._messages = {...model.properties._messages,
      description: 'The common client consumes an array, skips null items, and delegates object items to the SystemMessage parser. Other wire kinds remain unresolved.',
      'x-client-item-model': {$ref: '#/components/schemas/ClientSystemMessage'}};
  }
}
