# Instagram Client and Private API Vulnerability Research

> [!IMPORTANT]
> **Confirmed exploitable vulnerabilities: none in the current evidence.**
>
> This document records evidence-backed security hypotheses for the reverse-engineered
> Instagram Android client and its reconstructed private API surface. A recovered route,
> response field, exported component, or successful request is not by itself a vulnerability.

This is independent security research and is not affiliated with or endorsed by Meta or
Instagram. It is a research ledger, not a security advisory.

## Scope

| Item | Value |
| --- | --- |
| Android package | `com.instagram.android` |
| Client version | `451.0.0.53.80` (`385713116`) |
| Base APK SHA-256 | `4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b` |
| Evidence | Static client analysis and bounded, read-only observations recorded in this repository |
| Last reviewed | 2026-10-30 |

The target and acquisition boundaries are recorded in
[`apps/instagram/REPORT.txt`](apps/instagram/REPORT.txt#L1-L13). This document covers:

- the reverse-engineered Instagram Android application;
- client-to-server request construction and authentication behavior; and
- authorization, privacy, and integrity questions in the reconstructed private APIs.

It intentionally excludes the local workbench, proxy, web interface, build tooling, and
other code created for this repository.

## Evidence standard

The committed reconstructed catalog contains 679 documented operations and 777 unresolved
method paths. It records 120 bounded live-success observations, but zero complete server
contracts have been established. See
[`coverage.json`](apps/instagram/api/coverage.json#L2-L18) and the
[contract limitations](apps/instagram/docs/CONTRACT-RECOVERY.md#L79-L88).

The following labels are used throughout this document:

| Label | Meaning |
| --- | --- |
| **Confirmed** | Reproduced with controlled accounts, negative controls, current-version evidence, and a demonstrated security impact. |
| **Candidate** | A relevant client behavior or attack surface is established, but the security failure or impact is not. |
| **Observation** | A design or hardening detail that informs review but is not a vulnerability claim. |
| **Not established** | Available evidence includes a mitigating control or is otherwise insufficient to support the claim. |

Impact ratings below are conditional estimates, not CVSS scores. They describe the impact
that could exist **if** the missing security condition is demonstrated.

## Research summary

| ID | Review topic | Conditional impact | Current state |
| --- | --- | --- | --- |
| IG-APP-001 | Fail-open application-layer password envelope | Medium | Pinned DEX re-extraction and a narrow evidence-bound model corroborate the static finding; runtime dispatch, server acceptance, and credential exposure are unverified. |
| IG-API-001 | Recovery-material authorization review | High | Candidate: sensitive response parsing is established for account-security information; authorization and live behavior are unresolved. |
| IG-API-002 | Direct-message collection authorization review | Not rated | Not established: the committed evidence does not yet recover object-identifier inputs for the relevant routes. |
| IG-API-003 | Pending-media ownership review | High | Candidate: account-scoped identifiers are established; cross-account behavior is untested. |
| IG-API-004 | Recovery-response privacy review | Not rated | Not established: recovery routes and a token-like request field are traced, but sensitive response fields and differential behavior are not. |
| IG-API-005 | One-tap and business-credential binding review | Not rated | Not established: the routes are traced, but nonce, token, device-identifier, enrollment, and session-binding contracts are unresolved. |

## IG-APP-001: Fail-open application-layer password envelope

**Status:** Candidate. Pinned static behavior matches the reviewed anchors and a narrow
reference model; runtime exploitability is unverified.

### What is established

The pinned DEX trace shows that the password wrapper can fall back when no usable server
public key is available or when `CryptoPubNative.encrypt` throws. In that branch, the
original password can be placed in a tagged version-0 envelope rather than encrypted by
`CryptoPubNative`. The wrapper output is then assigned to `enc_password` for
`accounts/login/`.

The offline harness subsequently re-extracted the reviewed methods from the pinned APK,
matched eight exact instruction fingerprints and selected reviewed data-flow anchors, and
evaluated a manually transcribed model with a fixed synthetic sentinel. The missing-key and
forced-encryption-error paths produced a version-0 `enc_password` containing the sentinel
once. A separate `PLAINTEXT_WITH_TAGGING` state discarded the modeled encrypted result and
produced a `#PWD_TRANSIENT` version-0 field containing the sentinel once. The synthetic
encrypted control used version 4 and did not contain it. The harness exposed no dispatch
path and recorded zero external-action attempts. The pinned-APK mode also verified that the
wrapper's `A0N` selector maps to integer 3 and therefore to `#PWD_INSTAGRAM`.

Relevant evidence:

- fallback implementation: [`login-trace.json`](apps/instagram/evidence/login-trace.json#L1961);
- fallback mode initialization: [`login-trace.json`](apps/instagram/evidence/login-trace.json#L2607-L2609);
- missing-key and encryption-error branches: [`login-trace.json`](apps/instagram/evidence/login-trace.json#L3376-L3385) and [`login-trace.json`](apps/instagram/evidence/login-trace.json#L3541-L3550);
- `accounts/login/` and `enc_password` data flow: [`login-trace.json`](apps/instagram/evidence/login-trace.json#L6785-L6879);
- repository interpretation and explicit caveat: [`MOBILE-LOGIN-TRACE.md`](apps/instagram/docs/MOBILE-LOGIN-TRACE.md#L24-L28); and
- offline validator: [`validate-instagram-password-fallback.py`](scripts/validate-instagram-password-fallback.py), with usage and limitations below.

### What is not established

- The trace does not prove that a production request reaches the fallback branch.
- It does not prove that `PLAINTEXT_WITH_TAGGING` is issued or active in production.
- It does not prove that Instagram accepts the fallback envelope.
- It does not show a password transmitted outside TLS. The ordinary transport layer still
  applies.
- No credential exposure, authentication bypass, or account compromise was reproduced.

### Security hypothesis

If the production client dispatches this envelope and the server accepts it, application-layer
credential protection fails open. The password could then be visible to TLS termination,
intermediary processing, or request logging that the encrypted envelope was intended to
protect against.

### Safe validation

The non-dispatching validation is reproducible from the checked-in trace:

```sh
python3 scripts/validate-instagram-password-fallback.py
```

When the ignored pinned APK is available locally, the stronger mode re-extracts the reviewed
methods in memory and verifies the exact Instagram tag constant:

```sh
python3 scripts/validate-instagram-password-fallback.py \
  --apk apps/instagram/apks/base.apk \
  --scenario all \
  --show-synthetic-field
```

This is a manually transcribed evidence-bound model, not execution of the original
Android/JNI wrapper or reproduction of wire serialization. A later dynamic test would
require an isolated authorized device or emulator, networking disabled below the app, and
the same synthetic-sentinel inspection before dispatch. Any server-acceptance test requires
separate authorization and a disposable controlled account.

### Fix direction if confirmed

Fail closed, refresh the encryption key, and require the user to retry. Do not construct or
dispatch an envelope containing the original password after encryption failure, and ensure
the request body is excluded from all client, edge, and server logging.

## IG-API-001: Recovery-material authorization review

**Status:** Candidate. High-value attack surface; no authorization flaw is demonstrated.

### What is established

The client traces `POST /accounts/account_security_info/` and binds a response parser that
recognizes fields associated with backup codes, TOTP seeds, contact points, and trusted
devices. The committed catalog also contains `/accounts/regen_backup_codes/` as a route
candidate, but does not establish its method, request, response parser, or runtime use.

- account security operation and response model:
  [`coverage.json`](apps/instagram/api/coverage.json#L21-L65); and
- unresolved regeneration route candidate:
  [`openapi.json`](apps/instagram/api/openapi.json#L13217-L13239).

The account-security operation was deliberately excluded from bounded online testing
([audit](apps/instagram/api/online-validation-audit.json#L13-L17)). The committed audit does
not contain an executable regeneration operation.

### What is not established

The parser describes what the client can read; it does not prove that every field is returned,
that secrets are returned in reusable form, or that the server omits recent-password,
step-up, device, or session-freshness checks.

### Security hypothesis

A stolen, stale, or insufficiently bound session could expose account-recovery material or
regenerate backup codes without recent authentication, increasing account-takeover impact.

### Safe validation

First establish that the account-security operation is non-mutating; the existing audit
conservatively treats it as write-capable. Any later test must use a controlled account with
test 2FA and compare active, expired, revoked, and post-password-change sessions. Record only
status and field names; never retain codes, seeds, devices, email addresses, or phone numbers.
Do not invoke backup-code regeneration during non-destructive testing. Any such test belongs
on an expressly disposable account.

### Fix direction if confirmed

Require recent step-up authentication for recovery material, bind authorization to the
account and device, minimize returned secrets, invalidate stale sessions, and make any
regeneration event visible to the account owner.

## IG-API-002: Direct-message collection authorization review

**Status:** Not established. The committed evidence does not yet expose an object-input
contract suitable for an object-level authorization test.

### What is established

The client traces `GET /collections/list/` with a partial response model containing `items`
and `next_max_id`. One authenticated request without query parameters returned HTTP 200 with
an empty `items` array, which establishes only one observed session profile. The committed
catalog also contains `/direct_v2/collection/grid_view_items/` as a route candidate, but its
method, parameters, response, dispatch, and live behavior are unresolved.

- collection list route and response:
  [`openapi.json`](apps/instagram/api/openapi.json#L135617-L135648);
- bounded observation:
  [`read-validation-results.json`](apps/instagram/api/read-validation-results.json#L634-L655); and
- unresolved grid-view route candidate:
  [`openapi.json`](apps/instagram/api/openapi.json#L173855-L173879).

### What is not established

The committed evidence does not establish `thread_id` or `collection_id` as request fields
for these operations. No unrelated account requested a known controlled object. A 200
response with an empty list is not evidence of broken object-level authorization.

### Security hypothesis

If later contract recovery establishes caller-controlled object identifiers, missing thread
membership or collection-to-thread binding could disclose private shared media or collection
metadata to another account.

### Safe validation

Do not perform a cross-account test until the exact client request construction is recovered,
reviewed, and committed. If that prerequisite is met, create synthetic data in a controlled
A-to-B test thread, then request only the exact known object from unrelated controlled account
C. The expected result is a uniform denial or empty response. Never enumerate identifiers or
use real conversations.

### Fix direction if confirmed

Authorize every collection read against the authenticated account, current thread
membership, and the collection's canonical thread. Do not rely on identifier entropy, and
return uniform errors that do not reveal object existence.

## IG-API-003: Pending-media ownership review

**Status:** Candidate. Ownership binding is unresolved.

### What is established

The reconstructed client uses independently supplied identifiers across pending-media flows:

- `POST /media/configure_to_clips_cover_image/` takes `clips_media_id` and `upload_id`
  ([evidence](apps/instagram/api/coverage.json#L19879-L19918));
- `POST /media/configure_to_cutout_sticker/` takes `upload_id`
  ([evidence](apps/instagram/api/coverage.json#L19930-L19980)); and
- `POST /media/get_upload_status_REST/` takes `post_client_id`
  ([evidence](apps/instagram/api/coverage.json#L20042-L20075)).

Authentication, signing, ownership rules, and live behavior remain unresolved
in those entries. These flows were not executed by the bounded validator.

### What is not established

There is no evidence that identifiers are guessable, transferable between sessions, or
accepted when owned by another account. No draft or upload was read or modified across
accounts.

### Security hypothesis

If upload, media, and session ownership are not jointly enforced, one account could inspect
pending state or modify another account's unpublished draft configuration.

### Safe validation

Use two owned accounts with synthetic, unpublished, disposable drafts. Begin with upload
status and a cross-account negative control. Exercise configuration operations only on
sacrificial drafts, verify rejection before publication, and inspect only controlled draft
state. Do not guess or enumerate identifiers.

### Fix direction if confirmed

Bind every pending-media identifier to the authenticated account and upload session, verify
that related identifiers share the same owner, and reject mismatched or expired objects
before any state change.

## IG-API-004: Recovery-response privacy review

**Status:** Not established. No sensitive response contract, differential behavior, or
personal-data disclosure is present in the committed evidence.

### What is established

The committed catalog contains `/accounts/send_password_reset_link/` as a route candidate,
but does not establish its method or runtime use. It traces
`POST /accounts/contact_point_prefill/` with the token-like request field `big_blue_token`
and a `usage` field; the response contract and live behavior remain unresolved.

- unresolved password-reset route candidate:
  [`openapi.json`](apps/instagram/api/openapi.json#L14436-L14458); and
- contact-point prefill operation and current limits:
  [`coverage.json`](apps/instagram/api/coverage.json#L226-L255).

### What is not established

The current committed corpus contains no response fields for either surface, no
registered-versus-unregistered comparison, no returned contact value, and no evidence that
the token can be replayed or used for another account.

### Security hypothesis

Response fields, size, status, or timing could reveal account existence or recovery
capabilities. Weak token-to-account binding could disclose excessive contact information.

### Safe validation

Do not test the unresolved password-reset route until the exact official-client request is
recovered and reviewed. If that prerequisite is met, make one rate-limited comparison between
an owned account and a reserved nonexistent identifier. Compare only status, root field names,
coarse size, and broad timing. Never trigger resets for third parties. Test token binding only
with tokens and accounts owned by the researcher, and redact all values.

### Fix direction if confirmed

Return uniform recovery responses, mask contact points, bind prefill tokens to their account,
device, purpose, and short lifetime, and enforce rate limits without introducing a timing
oracle.

## IG-API-005: One-tap and business-credential binding review

**Status:** Not established. Relevant routes are traced, but credential-bearing request or
response fields are not established in the committed evidence.

### What is established

The client traces `POST /accounts/fetch_onetap/` and binds a response parser, but no request
or response fields have been recovered in the committed catalog. It also traces
`POST /ads/promote/fetch_business_user_access_token/`; despite the route name, its response
contract and live behavior remain unresolved.

- one-tap operation and current limits:
  [`coverage.json`](apps/instagram/api/coverage.json#L492-L524); and
- business-token route and current limits:
  [`coverage.json`](apps/instagram/api/coverage.json#L2659-L2695).

### What is not established

No nonce, token, linked-profile field, or device-identifier field is established for these
operations in the committed snapshot, and nothing crossed account or device boundaries.
Server-side enrollment, session, attestation, or asset-authorization checks remain unknown.

### Security hypothesis

If later contract recovery establishes replayable client identifiers without enrollment and
session binding, an unenrolled device profile could receive a login nonce or linked-account
metadata. Weak session-to-business binding could expose a credential for an asset the session
does not control.

### Safe validation

Do not perform a binding test until the exact official-client request and response contracts
are recovered and reviewed. If that prerequisite is met, use two owned accounts and isolated
device profiles, with only one profile enrolled for one-tap login. Swap only those controlled
profiles' identifiers and require the unenrolled profile to receive neither a nonce nor
linked-profile metadata. Do not redeem a returned nonce or use a returned business token
against another API. Discard any secret response after recording presence and type only.

### Fix direction if confirmed

Bind nonces and tokens to the authenticated account, enrolled device, intended asset,
purpose, and short expiration. Make them single-use and require server-side authorization
again when they are redeemed.

## Protocol observations that are not findings

### Literal `SIGNATURE.` envelope

For operations whose transport trace selects the reconstructed `signed_body` branch, the
model serializes parameters after a literal `SIGNATURE.` prefix; that branch does not
calculate a cryptographic signature
([contract evidence](apps/instagram/docs/CONTRACT-RECOVERY.md#L51-L63),
[implementation](apps/instagram/api/request-transports.mjs#L20-L38)). The committed evidence
does not establish that this envelope alone is an authentication or integrity boundary.

This does **not** establish a signing bypass. Authorization headers, session state, object
authorization, request limits, and other server-side controls may be the intended security
boundary. Treat this only as a reason to verify that client-supplied identity fields and
objects are authorized independently of the envelope.

### State-changing operations represented as `GET`

The semantic review blocks eight `GET` routes whose names suggest mutations, moderation
changes, or recovery actions
([blocked list](apps/instagram/api/online-read-safety.json#L1-L12)). The repository correctly
notes that a `GET` verb alone does not make a route safe
([validation policy](apps/instagram/docs/READ-VALIDATION.md#L3-L13)).

This is not yet a CSRF or cache-poisoning finding. The server-side mutation semantics and
credential transport are unknown; classic browser CSRF may not apply when explicit native
authorization headers are required.

## Android application surfaces: investigated but not established

The manifest contains 109 components explicitly marked `exported="true"`; 94 lack a
manifest-level component permission. Those counts are discovery inputs, not vulnerability
counts. Runtime enabled state, intent/URI validation, binder gates, signature checks, and
caller verification must be considered
([baseline](apps/instagram/REPORT.txt#L24-L30)).

| Surface | Evidence | Current conclusion |
| --- | --- | --- |
| Deep-link routing | The large URL router is exported but statically disabled; the enabled main activity accepts a limited set of custom-scheme hosts ([manifest](apps/instagram/evidence/AndroidManifest.xml#L324-L375), [router](apps/instagram/evidence/AndroidManifest.xml#L1427-L1468)). | Dynamic enablement and route validation deserve controlled testing, but no state/PKCE bypass, privilege change, or sensitive callback issue is shown. |
| Share and media ingestion | Feed, Story, Reel, and Clips share handlers are exported for Android sharing ([manifest](apps/instagram/evidence/AndroidManifest.xml#L4371-L4509)). | They are parser and denial-of-service fuzz targets; no missing type, grant, size, or lifetime check has been tied to an impact. |
| Direct-message IPC | `StellaDirectMessagingService` is exported without a manifest permission ([manifest](apps/instagram/evidence/AndroidManifest.xml#L3708-L3723)). | Decompiled code reviewed during this audit contains trusted-caller and messaging-permission checks before binder access. No bypass is established. |
| Sensitive content providers | Several providers are exported but statically disabled, including the logged-in-users provider ([manifest](apps/instagram/evidence/AndroidManifest.xml#L2025-L2029)). | Reviewed providers use same-key, family-app, or trusted-app delegates. Runtime enablement and signature enforcement still require negative testing. |
| WebViews | WebView activities exist, including `SimpleWebViewActivity`, but reviewed entries are non-exported ([manifest](apps/instagram/evidence/AndroidManifest.xml#L5361-L5369)). | No exported forwarding path to an attacker-controlled URL was found. |
| Backup and storage flags | The app sets `allowBackup="true"` with custom backup and extraction rules ([manifest](apps/instagram/evidence/AndroidManifest.xml#L170-L186)). | The flag alone does not prove that sensitive data is backed up or externally accessible. No data exposure is established. |

Likewise, route names such as `one_click_login_bypass`, normal MFA request fields, parsing
of `IG-Set-Authorization`, cleartext URL literals, and an HTTP 200 response are not security
findings without a demonstrated boundary failure.

## Candidate promotion criteria

A candidate should be promoted to a confirmed finding only when all of the following are
available:

1. Reproduction uses only accounts, devices, conversations, assets, and identifiers owned
   by the researcher or expressly provided for testing.
2. A negative control demonstrates the expected security boundary, followed by a minimal
   request that crosses that boundary.
3. The behavior is reproducible on the pinned client or a clearly identified current build.
4. The impact is demonstrated without retaining credentials, recovery material, personal
   data, messages, media, or raw response bodies.
5. Authentication, object ownership, device state, feature flags, and experiment state are
   documented well enough to distinguish a security defect from an incomplete contract.
6. The issue is reported privately through Meta's current security-reporting channel before
   exploit details or proof-of-concept code are made public.

## Research guardrails

- Use only controlled test accounts and synthetic data.
- Do not enumerate identifiers, scrape users, brute-force tokens, or trigger recovery for
  third parties.
- Do not send messages, publish media, make purchases, alter moderation state, or regenerate
  recovery material outside an explicitly authorized disposable environment.
- Record status codes, field names, and coarse behavior; discard secret values and personal
  content.
- Never commit sessions, authorization headers, cookies, passwords, MFA codes, device
  identifiers, raw account responses, or private URLs.
- Stop on rate limits, account challenges, unexpected state changes, or data belonging to
  another person.

The existing runtime work followed similarly bounded rules and deliberately excluded
recovery flows, account changes, messages, and other mutations
([review limits](apps/instagram/docs/REMAINING-READS.md#L7-L9)).
