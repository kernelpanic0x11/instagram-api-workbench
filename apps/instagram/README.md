# Instagram API Workbench

Browse the hosted Swagger catalog at [ig.beehivewebstudio.com/swagger.html](https://ig.beehivewebstudio.com/swagger.html). The existing [bio site address](https://bio.beehivewebstudio.com/instagram/index.html) remains available. Authentication and execution run in the local workbench.

A local JavaScript Swagger UI and an evidence-linked reconstruction of Instagram's Android API surface. Built from static analysis of Instagram Android **451.0.0.53.80**, using [REA](https://github.com/morluto/rea), JADX, and custom DEX analysis scripts.

**679 HTTP operations · 1,456 normalized paths · 777 unresolved-method route candidates**

Swagger includes all 679 traced operations. The **Operation coverage** panel lists
every operation, filters by remaining gaps, and links directly to its Swagger
entry. Offline DEX tracing recovered **788 logical request-field names across
399 operations**; the remaining request contracts still need investigation.
Paced [read validation](docs/READ-VALIDATION.md) records successful reads and
unsuccessful attempts separately. The
[coverage ledger](api/coverage.json) distinguishes those observations from
static evidence. No operation is claimed to have a fully recovered contract.

Response tracing now binds **603 normalized operations** to client parsers and
provides partial ordinary response models for **550 operations** in Swagger. The parser analysis follows
control flow, a verified shared field dispatcher, and bounded forwarding-parser
chains. Recognized response keys retain their DEX evidence; unknown value types,
nullability, nested shapes, server requiredness and exhaustive error responses remain
explicit gaps. This is not a complete server contract.

Finalized client encoding is traced for **298 operations**, including plain and
`SIGNATURE.`-prefixed `signed_body` envelopes. **626 operations** have error-parser
bindings. Shared message parsing distinguishes token shapes and client-required
`key`/`time` fields in system-message objects. Anonymous read checks also observed
HTTP 200 with JSON `status: "fail"`; HTTP success alone does not establish API success.

These counts describe recovered client configuration, **not endpoints verified to work against Instagram**. The project does not contain Instagram's server code, ranking algorithm, or a proven way to increase reach.

A [focused comment-keyword contract](docs/COMMENT-KEYWORDS-CONTRACT.md) now
documents a parameterless read construction, client-required response fields,
observed wire types, and HTTP-200 failure behavior. Open that GET operation in
Swagger to try it with your own verified Android connection. The
[post-keyword contract](docs/POST-KEYWORDS-CONTRACT.md) has also been traced through
two client callers and checked with a read-only authenticated request.

The optional [mobile HTTP/2 transport](docs/MOBILE-TRANSPORT.md) fixes a reproduced
case where Node fetch returned HTTP 400. Five formerly failing reads now succeed
through that backend; the ledger records **120 observed successful operations** after transport retests and reviewed
read-only searches/lists. The [online-testing audit](docs/ONLINE-TESTING.md)
distinguishes successes, failures and skipped operations; write-capable calls are
not executed under the current read-only scope.

## Run

Install Node.js 20.11 or later, then:

```sh
git clone https://github.com/kernelpanic0x11/instagram-api-workbench.git
cd instagram-api-workbench/apps/instagram/api
node server.mjs
```

Open **http://127.0.0.1:8766/**. Runtime dependencies and Swagger assets are already included; no npm install is required to browse or run the local server.

Everything is on that page:

- Standard Swagger UI with expandable operations and **Try it out**.
- An in-memory connection panel for an existing session cookie or bearer token.
- A manual GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS editor.
- Unresolved routes, GraphQL operation-name candidates, Bloks identifiers, and source evidence.

The JavaScript proxy forwards explicit requests to the connected profile: `https://www.instagram.com` for browser cookies or `https://i.instagram.com` for Android sessions. Relative routes default to `/api/v1`; explicit `api/`, `graphql`, and `rupload_` prefixes are preserved. This is a client routing choice, not a verified host/base-path binding for every candidate.

For browser-free mobile authentication, the optional [instagrapi adapter](api/AUTHENTICATION.txt) handles login and imports the resulting session into the workbench. It needs no APK or connected phone. Instagram may require a fresh two-factor code or account challenge. Saved session settings stay outside the repository in private application storage and can be reused on subsequent runs.

For browser login, install the optional helper once with `cd api && npm ci`, keep Google Chrome installed, and click **Open Instagram login** in Swagger. Sign in directly on Instagram in the separate Chrome window, then click **Verify authentication** and **GET my account settings**. Requests execute in that browser context; the workbench does not export cookies or save a browser storage-state file. Disconnect closes the temporary session. Advanced manual cookie/bearer entry remains available. Login challenges must be completed directly on Instagram. This is local browser automation, not Meta OAuth or a third-party login service.

**Connect & verify** verifies Browser sessions through the private `GET /api/v1/accounts/edit/web_form_data/` endpoint, returning only the authenticated username. Android sessions use `GET /api/v1/accounts/current_user/?edit=true`, including numeric account-ID matching when an expected ID is available. Browser verification cannot compare numeric IDs. A live Browser verification succeeded during development. Verification applies at the recorded time and does not prove permissions for every endpoint. Some operations need app headers, device context, signed payloads, or challenge completion. Mutating requests can change your account when executed.

### Finding your own session cookie

Log into Instagram in Chrome, open **DevTools → Network**, reload, and select an Instagram request. Copy its **Cookie** request header into the local connection panel. You can also inspect cookies under **Application → Storage → Cookies** ([Chrome documentation](https://developer.chrome.com/docs/devtools/application/cookies)). Preserve encoded values exactly. Leave Bearer token blank unless you already have one. Treat session credentials like a password; never share or commit them. A browser session may not work for every Android endpoint.

## What is included

| Area | Contents |
| --- | --- |
| [`api/`](api/) | Swagger UI, Node proxy, OpenAPI JSON/YAML, schemas, and tests |
| [`api/bulk-trace/`](api/bulk-trace/) | Conservative DEX register/receiver tracking and method/path observations |
| [`api/extraction/`](api/extraction/) | Reproducible route and operation-name extraction |
| [`visibility/TRACE.txt`](visibility/TRACE.txt) | Recommendation-status nudge, Account Status, and restriction-display trace |
| [`reels-trace/TRACE.txt`](reels-trace/TRACE.txt) | Reel publishing, audience/Trial parameters, duration warnings, response handling |
| [`REPORT.txt`](REPORT.txt) | Baseline package survey and bounded findings |
| [`evidence/`](evidence/) | Sanitized package metadata and static-analysis evidence |

The research found a client-side recommendation-status display flow and publishing constraints. It did **not** recover a shadowban decision algorithm or a reliable distribution boost. Historical trace notes preserve what was known at each stage; the API method trace subsequently established GET for the nudge endpoint.

## Evidence and limitations

The indexed corpus contained **1,178,767 DEX strings**. The bulk scanner decoded **807,462 methods across 23 DEX files** with no decoder errors and recorded 826 same-receiver configuration observations, yielding 676 distinct method/path pairs. Individually traced operations bring the published total to 679.

The scanner resets at control-flow boundaries and invalidates unknown mutations. An observation establishes that a method and route were configured on the same builder at a point in code; later overrides, dispatch, authentication requirements, status codes, payloads, and server availability remain unresolved.

Unknown methods remain unknown in OpenAPI. Generic request editors are not recovered schemas. Embedded native/JavaScript code, dynamic routes, and server-driven behavior are not exhaustively covered. The OpenAPI files are partial research artifacts, not an official SDK or supported contract.

Source base APK SHA-256:

```text
4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b
```

APKs, native/resource binaries, complete DEX dumps, device permission state, device installation paths, local process logs, and analysis-engine downloads are **not distributed**. Normalized REA records retain evidence IDs but omit raw provider transcripts and machine details. See [`PUBLIC_EXPORT.json`](PUBLIC_EXPORT.json).

## Development and validation

```sh
cd api
npm ci --ignore-scripts
npm run build
npm run validate
npm test
python3 bulk-trace/test_extract.py
```

Validation checks OpenAPI structure, JSON/YAML parity, template collisions, path parameters, operation IDs, and provenance. Tests exercise adversarial DEX tracking and mocked proxy forwarding, method/body/query preservation, credential clearing, origin/token checks, redirects, and error handling. No account credentials are used by the tests.

## Reproduce the analysis from your own APKs

Start with the complete [reproduction guide](docs/REPRODUCING.md) for tool installation, APK acquisition, the command sequence, and expected outputs. Use the [porting guide](docs/PORTING.md) to trace a new version and create a digest-bound mapping profile. APKs and downloaded engines remain your local inputs.

```sh
python3 scripts/doctor.py
npm ci --ignore-scripts --prefix api
python3 scripts/pull-apks.py --package com.instagram.android --output apks
python3 scripts/reproduce.py --apk-dir apks --output runs/current --routes-only --package com.instagram.android --version YOUR_INSTALLED_VERSION
```

For the exact reference base digest, omit `--routes-only` and its user-supplied labels to use the checked-in validated profile. Another APK is rejected by that profile before output is written; it must start route-only or use a newly reviewed profile. Runs go into new directories and do not overwrite the reference snapshot.

The output contains an inventory, deterministic string index, candidate catalog, method/path observations where traced, validated OpenAPI JSON/YAML, and a run receipt with input/profile/tooling/output hashes. Report regeneration supports sanitized public evidence; helper ranking reads the bundled gzip directly. See [VALIDATION.md](docs/VALIDATION.md) for checks actually performed.

Developer checks:

```sh
npm test --prefix api
python3 api/bulk-trace/test_extract.py
python3 scripts/test_reproduce.py
```

Static extraction needs no Instagram account or cookies. Optional method decompilation uses REA 6.5.0, a full JDK 17+, and a separately verified JADX headless MCP 0.7.1 engine. The setup steps and MCP examples are in the reproduction guide. Packed/native/server behavior remains outside the DEX pipeline.

## Local security

The server binds only to `127.0.0.1`. Credentials stay in process memory until disconnect or shutdown and are not written to files or browser storage. The proxy checks local host/origin and a per-process request token, permits only a fixed allowlist of HTTPS upstreams, does not follow redirects, strips upstream cookies, and bounds requests and responses. Do not expose it publicly or put a tunneling service in front of it. See [SECURITY.md](SECURITY.md).

## License and attribution

Original workbench code and analysis scripts are MIT licensed. Third-party Swagger assets keep their upstream licenses. Extracted identifiers, metadata, and decompiler evidence are research material; the MIT license does not grant rights to Instagram software. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Independent research project; not affiliated with or endorsed by Instagram or Meta.

The complete follow-up review of 37 previously unverified reads, including corrected requests and deferred contexts, is described in [REMAINING-READS.md](docs/REMAINING-READS.md).
