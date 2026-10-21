# Security

This is a local research workbench, not a hosted service. Keep the listener on loopback and do not tunnel or expose it to other users.

Use only sessions and accounts you control. Session cookies and bearer tokens grant account access. Enter them only in the local connection panel, never in issues, pull requests, example payloads, screenshots, or committed files. Disconnect clears server memory; stopping the server clears it too. Browser responses may contain account data after you explicitly make requests.

Report a security issue through GitHub's private vulnerability reporting feature if available. Do not post secrets or account data in a public report. Describe affected code and reproduction with synthetic credentials.

The proxy permits only the selected www.instagram.com or i.instagram.com host, does not follow redirects, validates local Host/Origin and an ephemeral request token, and strips upstream Set-Cookie headers. A local process with access to the same user environment is outside this isolation boundary. These controls do not make a public deployment safe.

The optional browser-login helper launches a separate temporary Chrome context.
It does not attach to a personal browser profile, export cookies, or save
Playwright storage state, traces, videos, screenshots, or HAR files. Sign in
only on Instagram in that window. API requests remain on www.instagram.com;
Disconnect closes the browser. Browser dependencies require npm ci; Chrome
login acceptance is controlled by Instagram. Manual session inputs remain an
advanced alternative. Do not commit browser profiles or authentication state.
