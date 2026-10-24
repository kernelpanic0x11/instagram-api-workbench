# Post-filter keywords: focused contract

`GET /accounts/get_post_filter_keywords/` reads the connected account's post-filter
keyword settings. It does not change settings. Open this GET operation in local
Swagger after verifying your Android connection; the proxy targets
`https://i.instagram.com/api/v1/accounts/get_post_filter_keywords/`.

Two pinned Android callers, `X.0HVZ.onViewCreated` and `X.0Qvj.Cya`, use the
`X.0221.A0K` GET factory, set this route and finalize the request without adding
endpoint parameters or a body. The first schedules the request; the second calls
the coroutine dispatcher. The traced plain-query path needs no `signed_body`.
Existing session/transport context still applies. Minimum authentication headers
have not been isolated.

Both callers select `X.0djX`, the same JSON parser as the comment-filter read:

| Field | Client acceptance | Observed wire shape |
| --- | --- | --- |
| `keywords` | Must decode as an array. Empty accepted. String-coercing item reader drops decoded nulls. | Empty array on one authenticated success; nonempty item types remain unknown. |
| `disabled` | Optional integer-reader result; missing value remains null internally. | Integer; semantics, enum values, coercion and wire nullability unverified. |
| `status` | Shared response handling. | String `ok` with HTTP 200 and application/json. |

Client-required `keywords` is documented separately from the observed wire
profile. Unknown response properties remain allowed. Shared error-parser models
cover client dispatch for HTTP >=400, including the special 403 path. No new
anonymous failure was probed for this endpoint; do not interpret the documented
HTTP-200 failure alternative as an endpoint-specific wire observation.

Regenerate pinned evidence and Swagger offline:

```sh
python3 apps/instagram/api/bulk-trace/trace-comment-keywords.py --endpoint post
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

With your own verified local connection, an optional single read saves only
allowlisted field types, status and metadata:

```sh
python3 apps/instagram/scripts/probe-comment-keywords.py --endpoint post
```

Instruction proofs are in `api/bulk-trace/post-keywords-evidence.json`; sanitized
runtime metadata is in `api/post-keywords-observation.json`. Keyword contents,
credentials and raw response bodies are never saved by this probe. Offline
reproduction removes live observations and regenerates static evidence from the
pinned cached APK, without a phone or account request.

This remains a bounded, tested client profile. Nonempty arrays, disabled variants,
conditional server validation, exhaustive errors and alternate Pando/native
response parsing need additional evidence. No mutating requests were performed.
