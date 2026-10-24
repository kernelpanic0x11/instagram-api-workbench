# Comment-filter keywords: focused contract

Use `GET /accounts/get_comment_filter_keywords/` in local Swagger after connecting
and verifying an Android session. The proxy resolves this to
`https://i.instagram.com/api/v1/accounts/get_comment_filter_keywords/`.
The inspected client construction supplies no endpoint query parameters, body,
or `signed_body`. Authentication/session context comes from the connection.
The exact minimum set of authentication headers has not been established.

The pinned caller `X.09eD.A00` constructs, finalizes and hands the request to the
coroutine dispatcher. Its JSON response parser is `X.0djX`. The ordinary JSON
parser accepts an object with these endpoint fields:

| Field | Client behavior | Observed server type |
| --- | --- | --- |
| `keywords` | Required to decode as an array; empty accepted. Items use a string-coercing reader; decoded nulls are skipped. Missing/non-array input throws. | Array; the live array was empty, so item wire types remain unknown. |
| `disabled` | Optional integer reader; absence leaves the decoded member null. | Integer in one success response. Meaning, enum values and wire coercion/nullability remain open. |
| `status` | Shared response handling. | String `ok` on authenticated success; `fail` on an anonymous HTTP-200 response. |
| `message` | Shared message-token handling. | String in the anonymous failure observation; text was discarded. |

Unrecognized fields remain allowed. The Swagger client model uses `required` only
for the parser's `keywords` requirement; the separate observed success profile
does not assert universal server requiredness. Known HTTP-200 success/failure
profiles coexist with permissive default and client-inferred 4XX/5XX models.
The shared special-403 path remains documented. Do not treat all HTTP 200 results
as successful application responses.

Evidence is tied to Instagram Android 451.0.0.53.80 and its source APK hash in
`api/bulk-trace/comment-keywords-evidence.json`. Regenerate instruction evidence:

```sh
python3 apps/instagram/api/bulk-trace/trace-comment-keywords.py
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

Optionally, with your own verified local Android connection, make exactly one
read-only check and retain only allowlisted metadata:

```sh
python3 apps/instagram/scripts/probe-comment-keywords.py
```

The probe never saves keyword values, raw bodies, cookies, tokens or response
headers. It reads through the connected local proxy and does not log in or change
settings. Offline reproduction regenerates static evidence and removes the live
observation. No phone is required when the pinned APK input is cached.

This is a usable, bounded client/response profile. Outstanding server-contract
work includes nonempty arrays, disabled variants, minimal authentication,
conditional validation, exhaustive errors and the alternate Pando/native parser
path. No settings mutation is needed or performed by this pass.
