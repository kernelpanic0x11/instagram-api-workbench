# Phone Home

An optional, independent Python companion for observing an authorized device during an app research session. It captures one target IP with tcpdump, retrieves matching AdGuard Home DNS records, and can record limited HTTP metadata from an explicitly configured mitmproxy session. The API workbench does not import or start this tool.

Capture is implemented. The `analyze`, `report`, and `render` commands are scaffolding and currently return a not-implemented error. A successful capture does not establish app-level attribution or full traffic visibility.

## Install and capture

Use Linux with Python 3.11+, tcpdump, GNU timeout, and permission to run tcpdump through noninteractive sudo. On a Raspberry Pi, install the system dependencies separately:

```sh
sudo apt-get install tcpdump python3-venv
cd tools/phone-home
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
cp env.example .env
chmod 600 .env
```

Fill in the AdGuard URL and credentials in `.env` if DNS enrichment is wanted. Without credentials, capture still preserves its packet file and records a DNS warning. Find the authorized phone's address using `tailscale status`; `192.0.2.10` below is a documentation placeholder:

```sh
.venv/bin/phonehome capture --app instagram --target 192.0.2.10 --duration 60 --iface tailscale0
```

The phone must already route internet traffic through the capture machine (for example, select that machine as its Tailscale exit node). Merely joining the same Wi-Fi is insufficient. For a LAN gateway capture, specify the relevant interface using `--iface`. This package does not change routing, DNS, or Tailscale settings.

Each run creates `runs/YYYYMMDD-HHMMSS-instagram/` with `raw.pcap`, `meta.json`, `dns.json`, and diagnostic output. Existing run directories are refused before modifying the packet file. Keep all run files private and out of Git.

The timer begins when tcpdump readiness is observed; initial packets may precede that timestamp by the short reporting/poll delay. Metadata distinguishes complete, empty, lossy, partial, and failed-start runs. Byte accounting and flow analysis are not implemented in this package yet.

## Visibility and DNS

Only the specified IP is captured, so a separate address family is outside that run. Device-wide capture can contain background apps. TLS and QUIC encrypt HTTP paths, headers, and bodies; some handshakes expose a hostname. A packet capture alone cannot recover encrypted request URLs.

Tailscale's default exit-node DNS proxy can handle requests before the TUN interface and forward them without retaining the original client address. Zero DNS packets on `tailscale0` does not prove that the app uses a private DNS resolver. Direct DNS routing must be verified separately. The AdGuard client follows pagination cursors, checks time boundaries, and includes only records with the exact target client IP.

## Optional HTTPS metadata recorder

Use this only on an authorized device configured to trust the test proxy. Install mitmproxy separately; it is not a required package dependency. The recorder addon is `scripts/record_https_metadata.py`:

```sh
PHONEHOME_MITM_LOG=runs/proxy-demo/requests.ndjson \
  mitmdump --listen-host 127.0.0.1 --listen-port 8888 \
  -s scripts/record_https_metadata.py
```

For a phone, choose a reachable interface deliberately and configure the phone's proxy and test CA. The tool does not install certificates or alter proxy settings. Restore those settings when finished. Apps can ignore the proxy or reject its certificate.

Records contain method, hostname, path without query parameters, response status, timestamps, addresses, and content byte lengths. Headers and bodies are omitted. Paths can still contain sensitive identifiers; output is private research evidence, not a public export.

See [Instagram traffic observations](../../apps/instagram/docs/PHONE-HOME.md) for the distinction between native-app and browser observations.

## Tests and third-party data

```sh
.venv/bin/python -m pytest -q
```

Tests use synthetic documentation addresses and mocked subprocesses/HTTP flows. Live DNS attribution and interception require separate device verification.

The vendored Disconnect tracker list is **CC BY-NC-SA 4.0**, not MIT. Its license is at `phonehome/data/DISCONNECT-LICENSE`; refresh it using `python scripts/update_trackers.py`. Classification using that list is not implemented yet. Original package code follows the repository's root license.
