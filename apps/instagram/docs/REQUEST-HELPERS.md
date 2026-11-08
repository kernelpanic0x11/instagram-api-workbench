# Reviewed request helpers and encoding recovery

The earlier offline pass added six finalizers and one parameter helper from the pinned
Instagram Android APK. Complete method instruction proofs are included in
api/bulk-trace/shared-contracts.json, bound to the exact APK and DEX hashes.
Unknown helper calls, branches, receiver escapes and unreviewed flag writes still
stop inference. No account or server requests are part of this pass.

| Helper | Reviewed construction behavior |
| --- | --- |
| X.0465.A0N(04x5,String,String) | A0F(key,value), then finalize with current envelope flag. Null values omitted. |
| X.0064.A0S(04x5,String) | A0F(max_id,value), then finalize with current envelope flag. Null values omitted. |
| X.0225.A0R(04x5,String,String) | AQE(key,value), set signing flag true, then finalize. |
| X.0221.A0V(04x5,String,String,boolean) | AQE(key,value), assign signing flag from fourth argument, then finalize. Unknown flag means no envelope inference. |
| X.0221.A0U(04x5,callback,String,String) | AQE(third,fourth), finalize with current flag, then attach callback to the completed request. |
| X.0224.A0P(04x5,String) | Set route, set signing flag true, then finalize. Old-route observations are detached; an unknown route cannot finalize an older one. |
| X.021X.A1L(04x6,Object,String) | Invoke Object.toString on second argument; AQE(third,result). Null receiver throws before setter; null string result is omitted. Does not finalize. |

A tracked builder supplied as the virtual toString receiver is invalidated: an
unknown override could change that builder. Normal string conversions retain
transport evidence only within the existing receiver/block boundaries. No object
or parameter values are retained. Logical and wire collections remain distinct.

Helper-call evidence records the actual helper as callee at the caller's DEX
instruction offset; forwarded_setter names the reviewed inner setter. The max_id
literal is attributed to the helper body. This avoids representing the helper
call's offset as though a direct AQE/A0F instruction occurred there.

Finalized encoding coverage increased from 245 to 298 of 679 operations. Recovered
request-field names increased from 687 across 358 operations to 788 across 399.
At that stage, 381 encoding paths still required further tracing. Evidence can describe
plain query, signed query, plain form or signed form, depending on HTTP method
and a proven flag. It does not calculate cryptographic signatures, guarantee
server acceptance, infer required fields, or establish complete endpoint contracts.

Regenerate from the pinned cached input:

```sh
python3 apps/instagram/api/bulk-trace/extract.py --reviewed-contracts
python3 apps/instagram/api/bulk-trace/trace-request-fields.py
python3 apps/instagram/api/bulk-trace/trace-shared-contracts.py
python3 apps/instagram/api/bulk-trace/trace-response-contracts.py
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

Synthetic regressions cover helper parameter positions, pagination's literal key,
true/false/unknown signing flags, callback placement, route replacement and unknown
routes, object conversion, and builder-alias virtual-call invalidation. Stronger
curated request schemas remain preserved. That earlier pass retained the then-current 100 live successes. The latest offline pass below retains 120.

## Shared setter and literal-key follow-up

The next pinned offline pass reviews twelve additional parameter helpers, including
primitive conversions, timezone_offset, media_id, device_id, guid, waterfall_id,
thread_id, route replacement and a non-builder session-helper return. Their complete
method proofs are part of shared-contracts.json. Decoding device_id also retains
0242.A04, A05 and its static byte-array initializer. Values are never evaluated.

Seven independently selected integer-switch lookup methods now resolve parameter
and response field names. A case is accepted only if the first instruction dispatches
the sole static integer input directly to a literal load and a return of that exact
register. Unknown indices, computed returns and unrelated method signatures remain
unresolved. Only used keys and compact physical switch-edge proofs are exported.
Literal origin remains bound to its own DEX hash and string index when called from
another DEX; the caller is not falsely assigned that string index.

At that stage, client encoding was traced for 343 of 679 operations; 336 remain unresolved.
The field pass recovers 980 field names across 441 operations. Response-parser
bindings reach 626 normalized operations, with 8,397 recognized response field
names by operation and 627 error-parser bindings. No server-requiredness or
cryptographic-signing requirement is inferred from these helper observations.

The reviewed A0N Boolean changes URL prefix selection, not parameter serialization.
Known assignments retain root_path_override and their bytecode evidence. False
does not by itself establish a default prefix; other flags remain relevant. Swagger
flags true root-relative variants, which the generic proxy does not automatically
reconstruct. Unknown flag values still stop transport inference.

Regression checks cover receiver positions, context aliases, non-builder returns,
unknown routes/indices, overwritten registers, cross-DEX literal provenance and
root-path flags. See literal_keys.py and the focused extractor tests for the exact
acceptance rules. This entire follow-up is offline: live success remains 120 and
no complete server contracts are claimed.

## Expanded route, request and response tracing

The reviewed mode of `extract.py` merges conservative method/route observations
with the additional pinned helper trace. It strips request fields, parser bindings
and transport data from the method-only export. Literal switch origins retain
the decoder DEX provenance. Symbolic `String.format` paths accept only a fixed
route prefix and string/integer placeholders, discard earlier builder facts, and
retain no formatting argument values. Other profiles keep the baseline mode.

The current export has 718 documented operations and 738 unresolved-method paths.
Request tracing recovers 1,092 field names across 473 operations and finalized
encoding for 382. Reviewed cache configuration leaves encoding evidence intact
but does not prove dispatch eligibility. The shared gzip wrapper is traced
separately from signing; per-operation compression is emitted only when the
complete caller trace proves its flag and POST body branch.

Response tracing distinguishes narrow and wide register writes, follows reviewed
field dispatch helpers, and checks that key and token facts still belong to the
reader's current value. Reader advances invalidate those facts. Delegated field
parsers require proven reader/key argument positions and cannot introduce nested
object keys as root fields. Returned JVM types are not treated as wire types.

The coverage ledger and Swagger now record ten evidence dimensions for every
operation and unresolved path. A live success is a bounded observation, and its
date remains separate from a later failed attempt. Three reviewed empty signed
GET inputs are bound to exact caller instructions by `reviewed-read-plan.mjs`;
all three succeeded in the latest check, bringing distinct successful operations
to 122. No server-complete or universally operational contract is claimed.
