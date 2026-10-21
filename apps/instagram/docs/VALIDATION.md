# Developer workflow validation

Checked on 2026-10-17 UTC. This records work actually performed, separately from instructions a developer can run.

## Environment

- macOS/POSIX host
- Python 3.14
- Node.js 26.7.0 and npm 11.19.0
- OpenJDK and javac 21.0.12.1
- ADB present; no fresh device acquisition was needed for the full extraction test
- Existing headless JADX MCP 0.7.1 JAR passed the pinned SHA-256 check

Minimum supported prerequisites are documented in REPRODUCING.md. These checks do not establish a full OS/runtime compatibility matrix. Linux/WSL/native Windows were not tested in this release.

## Automated checks

- 24 JavaScript workbench/proxy/authentication/browser tests.
- 8 synthetic DEX scanner tests covering receiver identity, aliases, branches, unknown calls and clobbers.
- 10 developer-workflow tests covering clean-copy report regeneration, omitted and raw evidence metadata, gzip helper evidence, safe missing-input handling, APK/profile mismatch rejection, draft profiles, missing-JADX process exit, engine overwrite protection, synthetic ADB acquisition, and an isolated route-only APK-to-OpenAPI run.
- OpenAPI structural validation and JSON/YAML parity.

The synthetic route fixture contains one string and no executable methods/classes; it is not an installable signed APK. Its result has one path, zero assigned operations, the measured fixture digest, no inherited reference schemas/traces, and a hosted view displaying its actual counts. Synthetic ADB tests verify acquisition logic without reading a phone or its private state.

## Full offline reference reproduction

The original locally held 13-APK snapshot was supplied to the new reproduction command in an isolated output directory. No APK or generated private workspace is committed.

Observed landmarks:

| Result | Observed |
| --- | ---: |
| Standard root DEX files | 23 |
| Indexed DEX string records | 1,178,767 |
| Decoded methods | 807,462 |
| Same-receiver configuration observations | 826 |
| Bulk method/path pairs | 676 |
| Decoder errors | 0 |
| Normalized OpenAPI paths | 1,456 |
| Operations after matching reference traces | 679 |
| Partial reference schemas | 5 |

The base digest matched the shipped profile. A separate rerun also confirmed that all configured method/field selectors occur in that exact APK. The workflow validated its generated OpenAPI and wrote input hashes, tooling/profile hashes, output hashes and a run report. This reproduces the static extraction landmarks; it does not establish live API availability or distribution effects.

## Clean export

The staged release was exported without Git metadata, APKs, analysis engines, local caches or npm dependencies. Dependencies were installed from the pinned lockfile in that exported tree. Build/validation, all 42 tests, the public-artifact scan, and the full offline APK-to-OpenAPI workflow passed from the clean tree. The only subsequent changes were this validation receipt, its machine-readable summary, release hashes, and hosted links to the documentation.

## Not established by these checks

- APK publisher signature authenticity, complete resource/native/packed-JS coverage, or full backend contracts.
- A fresh live device transfer with the new acquisition helper; its ADB behavior was checked with synthetic fixtures, while the real extraction used the already acquired snapshot.
- A new JADX decompilation session or a new upstream JAR download; existing pinned engine bytes and setup/error paths were checked.
- Live Instagram session stability, compatibility of every route, or ranking effects. Static reproduction uses no account credentials or API requests.

The checked-in traces remain historical observations. Publicly omitted raw operation/parameter metadata is represented as omitted during regeneration; the tooling does not fabricate it.
