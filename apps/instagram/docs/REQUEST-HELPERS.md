# Reviewed request helpers and encoding recovery

This offline pass added six finalizers and one parameter helper from the pinned
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
The remaining 381 encoding paths require further tracing. Evidence can describe
plain query, signed query, plain form or signed form, depending on HTTP method
and a proven flag. It does not calculate cryptographic signatures, guarantee
server acceptance, infer required fields, or establish complete endpoint contracts.

Regenerate from the pinned cached input:

```sh
python3 apps/instagram/api/bulk-trace/trace-request-fields.py
python3 apps/instagram/api/bulk-trace/trace-shared-contracts.py
python3 apps/instagram/api/bulk-trace/trace-response-contracts.py
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

Synthetic regressions cover helper parameter positions, pagination's literal key,
true/false/unknown signing flags, callback placement, route replacement and unknown
routes, object conversion, and builder-alias virtual-call invalidation. Stronger
curated request schemas remain preserved. The live-success count stays at 100.
