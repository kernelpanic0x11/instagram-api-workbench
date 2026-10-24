# Online testing within read-only scope

The account owner's testing constraint is explicit: do not change or delete
anything. Online execution therefore stays read-only. No messages, edits,
creations, deletions, moderation changes or challenge/recovery triggers are sent.
A GET verb is not sufficient evidence of read-only behavior. Each execution plan
requires semantic review, and online-read-safety.json blocks known change/security
routes even if their extracted method is GET.

The latest pass tested 24 new finite search, configuration, catalog and list GETs
through the already verified local Android HTTP/2 connection. Thirteen returned
HTTP 200 application/json with status ok; four returned 400 and seven returned
404. The recorded successful-read total is 113. No rate-limit, authentication,
account-protection or transport stop occurred. These counts combine historical
observations with the new pass, not 113 fresh tests performed simultaneously.

The APK-bound plan is api/online-read-plan.json and the sanitized observations are
api/online-read-results.json. Queries use only public test terms, small limits
or explicitly reviewed Boolean flags; omitted inputs remain a test limitation.
No private identifiers, raw responses, response values, headers or credentials
are saved. There is no automatic login, retry or pagination. The runner checks
application status rather than treating every HTTP 200 as success.

```sh
python3 apps/instagram/scripts/validate-read-endpoints.py --online-reviewed-reads --limit 20
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
```

Recorded attempts are skipped when the command is repeated. Account-protection
and transport stops cannot be automatically resumed. Offline reproduction removes
live observations and regenerates the audit without claiming runtime success.

api/online-validation-audit.json accounts for every one of the 679 documented
operations. States distinguish successful reads, tested/unverified reads, skipped
write-capable methods, skipped side-effect/security risks, and unreviewed reads
that may need request fixtures or context. It preserves check dates so older
successes are not presented as fresh guarantees. The 777 unresolved-method path
candidates are not executable operations and are outside this 679-operation audit.

The audit does not establish that all operations work online. In particular,
POST is left unexecuted under this scope even if some POST endpoints may be
read-like internally. Those need separate tracing and an appropriately scoped
review; the present instruction authorizes no account changes. Successful reads
also do not establish complete contracts, exhaustive errors, or feature access.

## Corrected-input follow-up

Five additional HTTP-400 reads were reviewed in the pinned APK. Three corrected
requests succeeded: direct empty state (session-derived user_id and combined-unit
flag true), fan-club category members (most_recent and Boolean flags), and sticker
tray section (STORIES, section_name=custom_stickers). The section key resolves
through 0122.A00(0x49); category values come from 0GsX.toString. Evidence is retained
in bulk-trace/read-repair-evidence.json and read-repair-contracts.json.

Sanitized observations in api/second-read-repair-results.json bring the aggregate
to 116 successful reads and 37 tested/unverified operations. The earlier 113 count
above describes the preceding batch. These are historical observations, not a
simultaneous fresh test of every route. Multiple inputs changed together, so this
does not establish which input the server requires. No account changes were sent.

Ranked recipients remains deferred pending verified mode values; content
inspiration remains deferred pending a verified entry_point. Neither was retried.
The follow-up runner skips recorded attempts, respects protection stops, reads the
existing session locally without login, and stores only query keys and response
shape metadata. The user ID never enters the result artifact or public plan.

## Complete review of the remaining 37

All 37 previously unverified GET operations have now been reviewed against pinned
caller bytecode. Twelve evidence-backed corrections were retested once: four
succeeded, two returned 400, five returned 404 and one returned HTTP 200 with
status fail. Twenty-five remain deferred with per-operation reasons. The current
aggregate is 120 successful reads and 33 tested/unverified operations. No
rate-limit, authentication, protection or transport stop occurred in this batch.

See [REMAINING-READS.md](REMAINING-READS.md), api/remaining-read-review.json and the
generated api/remaining-read-audit.json. Historical counts above describe earlier
batches. Retesting a corrected request does not prove individual requiredness or
full contracts, and a 404 does not establish permanent route removal.
