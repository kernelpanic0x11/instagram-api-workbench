# Review of ten HTTP-400 reads

This pass reviewed ten APK-backed request constructions after the initial 121-read
validation. Three changed requests were justified and retested. All three still
returned HTTP 400 with text/html responses; the successful-read total remains 51.
Their recovered parameters did not, by themselves, establish a working request.
The cause of the remaining failures is unresolved.

| Read | Recovered requirement or finding | Action |
| --- | --- | --- |
| Notification settings | Optional nonempty content_type; enable_ig_new_settings serialized true/false on the traced path. | Retested false; still 400. |
| Suggested hashtags | used_hashtags is a comma-joined list, including empty string for an empty list. | Retested empty list; still 400. |
| Map search null state | GET construction enables the signed_body query envelope. | Retested SIGNATURE.{}; still 400. |
| Controls-filtered media | JSON array of objects containing m_pk from caller media IDs; outer key is encoded and unresolved. | No fabricated media inputs or query key. |
| Contact-upload setting | Helper adds device-derived phone_id plus another key/value from Android context; caller also sets A0Y. | Device context and encoded key need deeper tracing. |
| Recent music searches | product from surface enum, browse_session_id from caller, empty search_session_id; conditional encoded Boolean key. | No invented browse-session context. |
| Threads activity count | threads_app_version comes from installed com.instagram.barcelona package version through a nullable setter. | No invented installed version. |
| Message settings v2 | Reviewed factory/route/finalizer adds no endpoint query fields. | No corrected construction identified. |
| Last-password-change timestamp | Root-relative A0N route flag, explicit api/v1 prefix. | Proxy already preserves prefix; no path correction identified. |
| Embed opt-out setting | Same root-relative flag and explicit-prefix behavior. | Proxy already preserves prefix; no path correction identified. |

Client presence rules are separate from server requiredness. The unknown encoded
Boolean key is recorded as unresolved metadata, never as an executable Swagger
parameter. Empty-list tests do not prove nonempty values or all feature access.
No mutating request or account-setting update was performed.

`api/read-repair-contracts.json` contains reviewed facts and caller signatures.
`api/bulk-trace/read-repair-evidence.json` contains APK-hash-bound instruction
proofs, including request helpers and the shared finalizer. Regenerate offline:

```sh
python3 apps/instagram/api/bulk-trace/trace-read-repairs.py
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

`api/read-repair-results.json` retains only query-key names, statuses and response
shape metadata. Original failed attempts remain in read-validation-results.json;
Swagger retains both in x-read-validation-history. No account values, raw bodies,
response headers or credentials are saved. Offline reproductions remove runtime
observations while regenerating the pinned static evidence.

The optional retest-read-repairs.py script runs only the three reviewed GET
corrections through an already verified local Android session, skips recorded
attempts, and stops for transport/authentication/account-protection failures.
Repeating unchanged requests is not part of the investigation workflow.

## Transport follow-up

The [mobile transport investigation](MOBILE-TRANSPORT.md) subsequently reproduced
a working HTTP/2 path. Notification settings, suggested hashtags, map search,
message settings and embed opt-out now have status-ok read observations, bringing
the ledger to 56. The original HTTP-400 outcomes above remain historical evidence.
