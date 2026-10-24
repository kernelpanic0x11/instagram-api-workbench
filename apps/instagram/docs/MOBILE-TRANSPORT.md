# Mobile transport: a reproduced HTTP-400 fix

Notification settings now succeeds through the optional mobile HTTP/2 backend.
A paired read used the same saved session, application-header payload, URL and
`enable_ig_new_settings=false` query. Node fetch returned HTTP 400 text/html;
the local HTTP/2 worker returned HTTP 200 application/json with status ok.
This isolates a difference in the transport implementation bundle, not a specific
TLS fingerprint, HTTP version rule, encoding rule or Instagram enforcement policy.

The pinned APK's shared finalizer selects default host i.instagram.com through
X.03yq.A00 and prefixes this caller's relative route with /api/v1. The reviewed
caller uses GET and query parameters, not a request body or signing envelope.
These URL/method rules matched the proxy. Static instruction evidence is in
api/bulk-trace/read-repair-evidence.json.

A separate header-policy comparison found dropped SDK headers: IG-U session
headers, X-Meta-Usdid, Accept-Language, Priority and X-Tigon-Is-Retry. Preserving
them alone did not fix the read. The adapter and proxy now share a checked-in
request-header-policy.json so both preserve the same supported application
headers. Host, Connection, framing/length and compression headers remain managed
by the HTTP implementation. Authorization and Cookie have separate input fields.
SDK header compatibility is not a claim of exact native-APK header parity.

When the optional tools/instagrapi-venv/bin/python environment exists, server.mjs
uses mobile-transport.mjs for requests to i.instagram.com. The Python worker uses
the pinned SDK's no-retry curl HTTP/2 adapter with certificate verification enabled.
It receives URL, method, headers and body through stdin; it does not load saved
settings, log in, solve challenges or write state. One worker handles one request.
Request bodies are limited to 10 MiB and responses to 32 MiB. Redirects are never
followed, and the only upstream host is i.instagram.com. Decoded response bodies
are returned without stale Content-Encoding/Content-Length headers.

Browser-profile requests continue through their existing transport. Without the
optional Python environment, the workbench uses Node fetch; the observed transport
limitation may then recur. Install the optional dependencies using the existing
AUTHENTICATION.txt setup and restart the server to enable the backend.

Credentials and response bodies cross local process pipes in memory. They are
never passed as command arguments, explicitly added to environment variables,
logged, or written to files by the transport. Worker diagnostics are discarded;
public errors use fixed text. Existing sessions remain private application data.

Sanitized comparison artifacts:

- notification-transport-observation.json: preserving headers alone still failed.
- notification-sdk-transport-observation.json: direct SDK transport succeeded.
- notification-http-transport-comparison.json: paired Node/HTTP2 comparison.
- transport-validation-results.json: notification success plus four successful
  follow-up reads on the fixed main proxy (hashtags, map search, message settings,
  embed opt-out). No response values were retained.

The initial transport follow-up reached 56 successful reads; consult the coverage
ledger for the current total and READ-VALIDATION.md for the broader retest. Prior 121-read and three-correction records
remain intact, and Swagger retains attempt histories. These results do not prove
a complete server contract or that every other failed endpoint shares this cause.
Offline reproduction removes live transport observations while retaining code,
static evidence and regression checks. No phone is needed.
