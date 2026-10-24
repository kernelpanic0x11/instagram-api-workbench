# Request and response contract recovery

All 679 traced operations are represented in Swagger. They remain partial
reconstructions, not complete server contracts. Consult `api/coverage.json` for
the separate request-field, response-model, parser-binding and live-check levels.

Request tracing recovers literal keys attached to the same request-builder
receiver within a basic block. It stops across unknown mutations and control-flow
boundaries. Missing keys do not establish that a request is parameterless.

Response tracing binds a static parser to a known request factory argument.
The factory methods and parser adapters are pinned to the exact source APK.
For supported JSON parsers, a control-flow analysis tracks keys read from the
input reader to literal `String.equals` comparisons. At joins, conflicting
register facts are discarded. Multiple key-reading sites are skipped to avoid
flattening nested inline parsers. The verified shared response dispatcher is
traced separately. Forwarding parsers are followed only when they pass an
untouched input reader to a static parser instance before any branch, for at
most three delegate hops.

The generated response schemas include recognized property names and their
evidence. They permit additional properties and leave value schemas open.
A parser returning a Java String does not prove the server accepts only JSON
strings: client readers can coerce values. No server-required properties, closed
enums, nested shapes or status-code sets are inferred from names or return types.
The documented JSON response media type is a client-parser inference, not a
wire Content-Type observation. Manually traced response schemas are preserved.

Reproduce these passes offline from the repository root:

```sh
python3 apps/instagram/api/bulk-trace/trace-request-fields.py
python3 apps/instagram/api/bulk-trace/trace-response-contracts.py
python3 apps/instagram/api/bulk-trace/trace-shared-contracts.py
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

All traces reject APKs that differ from the validated input. Isolated route-only
reproductions omit these mappings and all reference-session runtime checks.
No credentials or runtime response bodies are used by these traces.

Completing the remaining contracts requires further helper/native tracing and
controlled runtime observations, ideally with dedicated test accounts and test
media. A single successful response cannot establish every required field,
possible response shape or error condition. Testing a mutation must be scoped to
its intended account effect; this pipeline does not execute endpoint batches.

## Encoding, presence and message rules

The pinned client yields 788 field names across 399 operations and finalized
transport evidence for 298 operations. Nullable setters omit null; primitive
setters serialize when invoked. Boolean setters differ: some produce true/false,
others 1/0. These are client presence rules, not proof of server requiredness.

The shared encoder puts GET parameters in the query and non-streaming POST
parameters in UTF-8 form data. The traced signed-envelope branch serializes
parameters under signed_body with the literal SIGNATURE. prefix; that branch
does not calculate a cryptographic signature. Exclusion lists, raw-value maps,
streaming multipart branches and other integrity mechanisms need separate
analysis. With a session user ID, the shared POST path adds _uuid and additionally
_uid when the envelope flag is enabled. The workbench does not synthesize these
values or automatically sign requests. Unknown builder mutations stop inference.

The message reader handles object.errors, skips a top-level array, and uses
string coercion for other token kinds. The separate _messages array contains
SystemMessage objects whose client parser requires decoded key and time fields;
null items are skipped. Client acceptance requirements are marked separately
from server wire constraints. Open schemas preserve unknown wire types.

## Error handling and observations

626 normalized operations have error-parser bindings. The client selects an
error path for HTTP status >=400. Its special 403 path parses the common response
and throws a status-bearing exception even if parsing succeeds. The generated
4XX/5XX schemas describe client parser selection, not an exhaustive list of
server statuses or a guarantee that every error body is JSON.

Two credential-free GET checks returned HTTP 200 with JSON status fail and no
authenticated identity. Only allowlisted status enums and field types were
saved; raw response bodies, headers, cookies and personal values were discarded.
These are failure observations, separate from authenticated read-only
success records in the coverage ledger, and do not identify the cause of every future failure.

A complete contract requires evidence for conditional server validation, account
experiments, nested shapes, media types and error variants. Static analysis of
one app version cannot prove those exhaustively. The coverage ledger therefore
continues to report zero fully established server contracts.

The [read-validation workflow](READ-VALIDATION.md) adds bounded observed wire
profiles to Swagger and preserves unsuccessful attempts without marking them as
working. Runtime observations are omitted from offline reproductions.

## Field-reader and nested-parser recovery

The response pass now records the first JSON-reader call on the exclusive prefix
of a successful String.equals branch. It requires the equals result to feed an
immediate if-eqz/if-nez, chooses only the equality-true edge, and stops at shared
joins, further branches, returns, unknown reader effects and a bounded prefix
length. An input-reader fact must reach the call. False-edge calls, shared cleanup
and overwritten readers are excluded. Token peeks are not field-value evidence.
Calls are labeled client_reader_calls; return_descriptor is a JVM descriptor,
not a JSON schema type. A String reader may coerce tokens, and a Boolean-returning
reader call may serve a predicate. No closed wire type or server requiredness is
inferred from these signatures.

This recovers reader-call evidence for 670 fields by parser, exposed across 387
operations (5,728 fields counted by operation). Three independently reviewed
nullable X.0D79 helpers bind to child parsers for PageInfoImpl, X.0IP4 and
ReelResponseItem. Their null-token branches and full instruction code units are
retained with APK/DEX hashes. Twelve field-reader sites have these child-parser
bindings; child schemas are linked only where their fields were recovered.
These links use x-client-nested-response-models, leaving wire schemas open.

Request recovery also retains fields configured before the first route/method
assignment. Later route or method changes still discard prior fields and detach
prior observations. The reviewed X.020p.A0K route-setting finalizer now supplies
transport evidence, raising encoding coverage from 218 to 245 operations.
Synthetic regressions check false edges, different/overwritten readers, joins,
initial-route field retention, and known/unknown route finalizers.

The remaining work includes 76 ordinary parser bindings, 53 error-parser
bindings, 381 finalized encoding paths, deeper nested shapes, encoded keys,
conditional client construction and server-side validation/error variants.
Those counts describe missing evidence, not necessarily unavailable APIs. The
100 live successes remain separate. No additional account requests were made
for this static pass. Mutation contracts require scoped fixtures and appropriate
test-account inputs before runtime validation; read-only observations cannot
establish their effects or error matrix.

The subsequent [shared-helper pass](REQUEST-HELPERS.md) adds six finalizers and
one conversion helper, raising encoding coverage to 298 and recovered fields to
788 across 399 operations. Earlier pass counts above are historical.
