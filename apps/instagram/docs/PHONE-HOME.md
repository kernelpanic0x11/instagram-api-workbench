# Phone Home traffic observations

[Phone Home](../../../tools/phone-home/README.md) is an optional device capture companion to the static API catalog. Static APK evidence, packet metadata, reverse-DNS enrichment, intercepted HTTP, and successful endpoint execution are different evidence classes; do not promote one into another.

## Native-app session

An authorized device capture during Instagram scrolling contained 52,351 IPv4 packets, 1,294,664 outbound IP bytes, and 62,725,981 inbound IP bytes over a first-to-last-packet span of 20.427790 seconds. IP lengths include protocol overhead and retransmissions. Six remote IPv4 addresses were observed. These measurements cover the selected device address, not solely the Instagram process.

The visible ClientHello hostname was `z-m-gateway.facebook.com`, associated with TCP and UDP traffic. No plaintext HTTP URLs or decoded MQTT frames were observed. Static APK evidence for an MQTT-backed realtime client does not prove that this particular connection carried MQTT.

Later PTR lookups suggested Instagram CDN and other Meta services. Those are time-dependent enrichment, not DNS queries recovered from the session. One PTR referenced WhatsApp, reinforcing the background-app attribution limit. The original capture and device addresses are intentionally excluded from this repository.

## Active HTTPS comparison

A separately configured test proxy decrypted ordinary browser HTTPS on an authorized Android device. The native Instagram app contacted relevant Instagram API/CDN hosts but ended TLS handshakes before HTTP requests were recorded. This demonstrates certificate rejection in that setup; the exact trust or pinning mechanism was not isolated.

Instagram Web in Chrome did produce decrypted HTTP metadata, including `POST /api/graphql`, `GET /data/manifest.json`, and static resource requests. Those are browser-client observations and do not validate the native Android API catalog.

The browser session also observed `POST /error/ig_web_error_reports/`, `POST /ajax/bz`, and `POST /ajax/qm/`. The first is path-explicit error reporting; the latter two are telemetry/metrics candidates. A path name alone does not establish the contents or purpose of every request.

No cookies, authorization headers, query values, request/response bodies, raw captures, or account identifiers accompany these observations. The optional recorder omits headers, query values, and bodies, but dynamic path segments can still be sensitive and must remain private.

## Current status

Packet capture and limited proxy metadata recording are implemented with offline tests. The Phone Home analyzer, report generator, classification/enrichment pipeline, and playback renderer remain unimplemented. Target-attributed DNS was not verified in the original session. These observations are research notes, not a completed end-to-end Phone Home release or proof that the native app was decrypted.
