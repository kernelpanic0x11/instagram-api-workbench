INSTAGRAM API — LOCAL JAVASCRIPT SWAGGER WORKBENCH

Use http://127.0.0.1:8766/ for everything.
Restart: cd api && npm start
Requires Node 20+. Viewer/manual proxy have no npm runtime dependencies.
Browser login additionally requires Google Chrome and npm ci in this directory.

USAGE
Recommended: Open Instagram login, sign in on Instagram, then Verify
authentication and GET my account settings. Cookies remain in the temporary
browser context. Disconnect closes it. No cookie copying is needed.

Advanced manual credentials:
1. Enter an existing Instagram session cookie or bearer token under Local Instagram
   connection. Optional JSON headers can include app User-Agent, X-IG-App-ID,
   X-CSRFToken and the other allowed app headers.
2. Connect & verify stores credentials only in server memory and immediately
   checks authentication. Credentials are not saved to disk or browser storage.
3. Browser verification uses accounts/edit/web_form_data/ and requires private
   account-settings JSON with a username. Android verification uses
   accounts/current_user/?edit=true and checks the numeric ID when expected.
   Browser verification cannot compare numeric IDs. See AUTHENTICATION.txt.
4. Expand an endpoint, select Try it out, supply the path/payload, and Execute.
   Or use the manual editor for GET, POST, PUT, PATCH, DELETE, HEAD or OPTIONS.
5. Disconnect clears credentials. Restarting the server also clears them.

All requests go through the fixed-allowlist Node proxy at /proxy to the selected browser or Android host.
Relative routes default to /api/v1. Explicit api/, graphql and rupload_ paths are
preserved. This default is a configurable-client design choice, not proof every
recovered route belongs on that host/base path. Other hosts are not supported.
Upstream response status/body is shown. Redirects are not followed. Requests have
30-second timeouts, 10 MiB body and 32 MiB response limits. Cookies and credentials
are not included in Swagger's generated curl snippets: the proxy injects them.

The proxy makes real requests when Execute is clicked. Mutating requests can
change your Instagram account. There is no mock or simulated success mode.
A live Browser account-settings GET and the corrected verifier succeeded during
development. A later session check redirected to login; recorded success does
not establish continuing session validity or compatibility with other APIs.
Invalid/expired sessions, checkpoints, app/device headers, signatures, rate limits,
and incomplete/changed endpoints can cause upstream failures. The application
neither obtains phone session credentials automatically nor synthesizes signatures.
Existing signed_body payloads can be entered in the manual editor.

COVERAGE
1,456 normalized paths; 679 GET/POST operations with traced client configuration;
777 unresolved-method paths; five partial schemas. Additional GraphQL/Bloks name
catalogs appear on the SAME Swagger page. Unknown verbs are visibly UNKNOWN and
never invented in the OpenAPI document. Manual method selection is user input.
676 method/path pairs came from conservative same-receiver basic-block tracing
(826 observations), plus prior individually traced operations. These prove that
client code configures a request at a point, not dispatch or server availability.
Generic request-body editors are NOT recovered request schemas.

Source: com.instagram.android 451.0.0.53.80; base.apk SHA256:
4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b
Corpus: 1,178,767 indexed DEX string records. This is not a complete Instagram
server contract. Native/packed JS, dynamic strings, server-driven routes,
request signing, payload schemas, and runtime behavior remain incompletely traced.

FILES
openapi.json / openapi.yaml: equivalent validated OpenAPI 3.1 documents.
index.html / live.mjs / live.css: standard Swagger UI plus connection/manual tools.
server.mjs / proxy.mjs: local JavaScript server and request forwarding.
bulk-trace/operations.json: static configuration evidence and limitations.
extraction/catalog.json: full candidate ledger with original strings and offsets.
schema-evidence/schemas.json: partial schemas with source excerpts.
evidence/: REA/JADX method evidence. Other referenced evidence lives in the parent
investigation directory; full extraction reproduction needs its APK/string corpus.

REPRODUCE FROM THE ORIGINAL INVESTIGATION DIRECTORY
python3 extraction/extract.py
python3 bulk-trace/extract.py
npm ci --ignore-scripts
python3 make-operations.py
npm run build
npm run validate
node --test proxy.test.mjs
python3 bulk-trace/test_extract.py
npm start

VALIDATION
JSON/YAML equality; OpenAPI validation; template collision, operation ID and path
parameter checks. Eight adversarial scanner tests and twenty-four proxy/authentication/browser/response-diagnostic tests
pass. Proxy tests cover methods, payload/query, credentials, origin/token checks,
redirect protection, response filtering and safe errors. Browser tests exercise
page loading, connection controls, operation rendering and unauthenticated errors.
Automated tests use synthetic credentials and mocked responses. The separate
live Browser verification did not persist credentials or account response data.

Pinned dependencies in package-lock.json. Swagger UI includes upstream licenses.
https://spec.openapis.org/oas/v3.1.0.html
https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
