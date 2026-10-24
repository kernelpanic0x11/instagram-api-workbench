# Reproducible read validation

The goal is 100 successful read operations. `api/read-validation-plan.json`
contains explicitly reviewed settings/configuration/list GET candidates. It
excludes mutations even when the extracted verb is GET, such as delete/reset,
report-undo, restriction triggers and spam-state changes. Merely having a GET
verb does not make a route safe to test.

`api/read-validation-results.json` records the actual outcomes. Swagger's
Operation coverage panel distinguishes observed successes, attempted reads that
were not verified, and untested operations. Use its filters and download the
ledger. Success means one HTTP-200 application/json object with status ok; it
neither establishes feature access nor completes the full server contract.

The runner uses only an already connected, verified local Android session:

```sh
python3 apps/instagram/scripts/validate-read-endpoints.py --limit 10
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

Each invocation performs at most 20 pending reads, two seconds apart. Existing
results prevent duplicate requests. It never logs in, sources credentials,
follows upstream redirects, paginates, automatically retries, searches, fetches additional
identifiers or executes POST/PUT/PATCH/DELETE. The current-user read uses edit=true;
other candidates initially send no endpoint query parameters. That is a tested
construction, not a declaration that all parameters are optional. Missing
parameters, app headers, endpoint retirement, feature eligibility and other
server conditions may prevent verification.

Rate limits, authentication expiry, challenge/checkpoint responses and transport
errors and HTTP 5xx responses stop the run. A protection stop cannot be automatically resumed. Do not
remove the stop marker just to force more requests. Once 100 distinct successes
are recorded, initial-validation mode sends no further requests. Explicit
transport-retest mode completes its frozen candidate set.

Only statically recognized root field names and JSON type metadata are saved.
Response values, arbitrary keys, numeric identifiers, nested account data, raw
bodies, response headers and credentials are discarded. Arrays retain only
observed item kinds, with no claimed item kind for empty arrays. Generated wire
schemas allow additional fields and do not infer universal requiredness from one
response. The parser's required fields remain a separate evidence level.

Offline reproduction omits these live observations. Cached APK tracing does not
require the original developer's account or a connected phone. Your own runtime
verification does require your own session and may have different outcomes.

## Recorded validation pass

The recorded pass attempted 121 distinct operations: 51 returned
HTTP 200 with JSON status ok; 70 were not verified. There was
no rate-limit or account-protection stop. This falls short of the 100-success
goal. Failed calls require further parameter/header/availability investigation;
this pass does not identify their causes. No additional requests are automatic.

A [focused follow-up](READ-REPAIRS.md) reviewed ten HTTP-400 reads. Three
evidence-backed corrections were tested and still failed; original and corrected
attempts remain separate. At that stage the verified-success count remained 51;
the later transport fix and retest are recorded separately.

## Explicit transport retest

After enabling the fixed mobile HTTP/2 backend, retest only reviewed candidates
whose earlier reads were unverified and which have no later recorded success:

```sh
python3 apps/instagram/scripts/validate-read-endpoints.py --retest-mobile-transport --limit 20
```

This mode writes mobile-retest-results.json instead of replacing earlier results.
It freezes the original candidate list so rebuilding Swagger between batches
cannot change the pass inventory. Recorded attempts are skipped on subsequent
invocations. Rate-limit, authentication, account-protection and transport stop
rules remain in force. No request parameters are guessed. Success observations,
unsuccessful attempts and their histories are merged into the coverage ledger
when Swagger is rebuilt. Offline reproductions omit the retest observations.

### Recorded HTTP/2 retest

All 65 remaining unverified candidates were retested once through the fixed
transport. 37 returned HTTP 200 application/json with status ok, bringing the
verified total from 56 to 93 of the 121 reviewed operations. The remaining 28
comprise 12 HTTP-400 responses, 15 HTTP-404 responses, and one HTTP-200 status-fail
response. No rate-limit, authentication, account-protection or transport stop
occurred. No additional candidates are automatically tested.

Earlier attempts remain in their original files and in Swagger's
x-read-validation-history. A later successful read replaces an earlier observed
failure-only HTTP-200 description; stronger curated response contracts remain
intact. Success still establishes a bounded read, not an exhaustive contract.

## Reaching 100 verified reads

The bounded additional plan tested eight new operations using APK-backed query
keys, the public term software, and small list limits. Seven returned HTTP 200
application/json with status ok, reaching exactly 100 successful reads. The runner
stopped at that target and left four planned candidates unexecuted. Profile-link
search returned HTTP 400 and remains unverified.

| Successful read | Tested public query |
| --- | --- |
| /users/search/ | q=software, count=3 |
| /tags/search/ | q=software, count=3 |
| /direct_v2/search_secondary/ | query=software |
| /direct_v2/get_presence/ | suggested_followers_limit=3 |
| /direct_v2/get_presence_active_now/ | recent_thread_limit=3, suggested_followers_limit=3 |
| /direct_v2/threads/broadcast/activity/ | thread_limit=3 |
| /direct_v2/search_gen_ai_bots/ | num_ai_bots=3 |

These are explicit tested inputs, not server defaults, required-field proofs or
accepted-range guarantees. Swagger exposes the public examples on the successful
operations. No response values, search-result identifiers or credentials were
saved. Only GET requests were executed, without pagination, automatic retries,
login attempts, rate-limit stops or account challenges.

The source-bound plan is api/additional-read-plan.json; actual observations are
in api/additional-read-results.json. The runner validates query keys against the
pinned APK's recovered fields and stops at the cumulative verified-read target:

```sh
python3 apps/instagram/scripts/validate-read-endpoints.py --additional-reviewed-reads --limit 12
```

It sends no more upstream reads after the recorded goal is reached. Offline
reproductions omit the runtime observations. The 100 successes are bounded live
reads; full server contracts remain partial.
