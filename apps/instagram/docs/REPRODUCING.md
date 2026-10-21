# Reproduce and extend the analysis

This guide starts with a Git checkout and your own APK inputs. It does not require an Instagram login for static analysis. Run all commands from the repository root unless a command says otherwise. This release was verified on macOS. The commands below use a POSIX shell; Linux/WSL need the same prerequisites and have not been verified in this release. The optional `rea-local` wrapper and MCP capture client require `sh`. Native Windows users can run the pinned REA MCP command directly in their MCP client instead.

## 1. Install and check the tools

| Task | Tools |
| --- | --- |
| Browse Swagger or run the manual proxy | Node.js 20.11 or later; no npm install needed |
| Rebuild extraction/OpenAPI, run analysis tests | Python 3.10+, Git, Node.js 20.11+, npm |
| Copy installed APKs from your own phone | Android SDK Platform Tools (`adb`) |
| Decompile and inspect methods | Full JDK 17+ including `javac`, REA 6.5.0, headless JADX MCP 0.7.1 |
| Optional local browser login/API testing | Google Chrome plus the optional Playwright npm dependency |

Install Node from [nodejs.org](https://nodejs.org/en/download), Python from [python.org](https://www.python.org/downloads/), Android [SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools), and a full JDK from your OS package manager or [OpenJDK](https://jdk.java.net/). Add their command-line tools to PATH. A Java runtime alone is insufficient for REA's Android provider.

```sh
git clone https://github.com/kernelpanic0x11/instagram-api-workbench.git
cd instagram-api-workbench/apps/instagram
python3 scripts/doctor.py
npm ci --ignore-scripts --prefix api
npm test --prefix api
python3 api/bulk-trace/test_extract.py
python3 scripts/test_reproduce.py
```

`doctor.py` prints the detected versions and returns a nonzero exit code for missing prerequisites. The last test command checks a clean copy, public report regeneration, gzip evidence handling, digest mismatch rejection, and a synthetic route-only extraction. The synthetic fixture is not an installable APK and is not a live Instagram test.

### Optional decompiler setup

The route/DEX pipeline below does not need a running decompiler. Install this lane when you need to inspect methods or validate mappings for a new APK:

```sh
python3 scripts/setup-jadx.py
export REA_JADX_MCP_JAR="$PWD/tools/jadx-headless-mcp-0.7.1-all.jar"
python3 scripts/doctor.py --android
```

The setup helper fetches the engine from its upstream release and checks the pinned SHA-256 before installing it. It refuses to overwrite a mismatching existing file. The engine JAR is ignored by Git. If Java is not found, set `JAVA_HOME` to your full JDK and put its `bin` directory on PATH.

The pinned JADX digest is `6e5eacf500b64292bfb73c49797c1958f6ee44646e43e868039ae7feb573ff75`. See [REA's Android provider setup](https://github.com/morluto/rea/blob/main/docs/android-analysis.md) and [the upstream JADX release](https://github.com/1013503897/jadx-headless-mcp/releases/tag/v0.7.1). The repository's `rea-local` launcher uses `npx --yes rea-agents@6.5.0`; npm downloads that pinned package on first use. REA and the engine are external dependencies, not bundled binaries.

## 2. Acquire your own APK snapshot

On a phone you control, enable Developer options and USB debugging, connect USB, unlock the phone, and accept its computer-authorization dialog yourself. Do not enable debugging on someone else's phone. [Android's ADB guide](https://developer.android.com/tools/adb) describes connection and authorization.

```sh
adb devices
python3 scripts/pull-apks.py --package com.instagram.android --output apks
```

With multiple devices, append `--serial YOUR_DEVICE_SERIAL`. The helper reads `pm path`, pulls base.apk and all installed split APKs, checks ZIP integrity, computes local hashes, and compares remote hashes when the device provides `sha256sum`. Its acquisition manifest says explicitly whether remote transfer hashes were verified. It does not read the app's databases, passwords, cookies or private data. It does not install, launch or modify Instagram.

An already-owned APK set can be placed directly in `apks/`, with its base named `base.apk`; keep split filenames distinct. No APKs are supplied by this repository. The helper refuses to overwrite an existing snapshot; use a new output directory for another version. Do not mix base/split files from different installations.

## 3. Choose the correct extraction mode

### Reproduce the reference version

The checked-in profile is bound to the exact analyzed base artifact:

- Instagram Android `451.0.0.53.80`
- Base SHA-256: `4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b`
- Mapping profile: [`api/bulk-trace/profiles/instagram-451.json`](../api/bulk-trace/profiles/instagram-451.json)

If you possess that exact base APK, run:

```sh
python3 scripts/reproduce.py --apk-dir apks --output runs/reference
```

Allow roughly 1 GB of free disk space per reference-sized run, plus the optional decompiler heap. The output directory must not already exist. The script copies the inputs and source into an isolated workspace, inventories/indexes APKs, extracts lexical candidates, traces method/path configuration, combines matching reference traces, and builds and validates OpenAPI JSON/YAML. It makes no account/API requests. It records input hashes, mapping-profile hash, relevant tooling hashes, Python/Node versions, decoder errors and output hashes in `run-manifest.json`.

On the original 13-APK snapshot, the expected landmarks are 1,178,767 DEX strings; 23 standard DEX files; 807,462 decoded methods; 826 configuration observations; 676 bulk method/path pairs; and 679 documented operations across 1,456 paths after the three individually traced operations are included. A different split set may change inventory totals even when the base matches. Do not use these counts as pass criteria for another version.

### Start with a different Instagram version

```sh
python3 scripts/reproduce.py --apk-dir apks --output runs/current --routes-only --package com.instagram.android --version YOUR_INSTALLED_VERSION
```

This produces a lexical catalog and OpenAPI paths with **zero assigned HTTP operations**. It removes the old manual traces/schemas from the new workspace. Version/package labels in this mode are supplied by you, not decoded from the manifest; the APK SHA-256 is measured independently. It does not reuse obfuscated helper names from the reference APK.

Follow [PORTING.md](PORTING.md) to validate a new profile. Then run another new output directory with `--profile path/to/your-profile.json` instead of `--routes-only`. If dependencies are not installed in the source checkout, `--install` explicitly runs `npm ci --ignore-scripts` in the new workspace. Otherwise the workspace reuses installed build dependencies locally.

## 4. Understand the command sequence

The wrapper runs these stages inside the new workspace:

```sh
python3 inventory.py
python3 index_strings.py
python3 api/extraction/extract.py
python3 api/bulk-trace/extract.py --apk apks/base.apk --profile api/bulk-trace/profiles/run-profile.json
python3 api/make-operations.py
node api/build.mjs
node api/validate.mjs
```

`bulk-trace/extract.py` is skipped for route-only runs. `make-operations.py` adds three manually traced reference operations and is used **only** for the original digest; do not run it against an unrelated APK. New profiles initially contribute only their newly traced bulk operations. Both inventory/index scripts fail before writing anything when no APK inputs exist.

| Output in the run directory | Meaning |
| --- | --- |
| `apks/` | Local copies of your input snapshot; never commit |
| `evidence/inventory-summary.json` | Archive, DEX, class and string counts |
| `evidence/all-dex-strings.jsonl.gz` | Deterministic gzip string index; generated locally |
| `api/extraction/catalog.json` | Lexical candidates with DEX provenance |
| `api/bulk-trace/operations.json` | Same-receiver method/path observations, coverage and errors |
| `api/openapi.json`, `api/openapi.yaml` | Equivalent validated API catalog |
| `run-manifest.json`, `RUN_REPORT.md`, `run-log.txt` | Reproduction receipt, result summary and commands |

The generated `api/target.json` supplies the new target labels and measured digest to the build. Reference files in your checkout are not overwritten. `runs/`, APKs, downloaded engines, authentication state and private logs are ignored by Git.

To browse a run's result, use a spare port if the reference server is running:

```sh
cd runs/reference/api
PORT=8767 node server.mjs
```

Open `http://127.0.0.1:8767/`. Static extraction needs no login. Only explicit live API requests need your own session; authentication does not make every candidate valid.

## 5. Continue with REA and inspect the code yourself

Use an MCP-compatible client configured with command `npx`, arguments `["--yes", "rea-agents@6.5.0", "--mcp"]`, and your `REA_JADX_MCP_JAR` environment variable. Confirm the server advertises its Android tools. REA setup does not itself install the JADX JAR.

Alternatively, on a POSIX host, start the included stdin capture client:

```sh
node visibility/rea-session.mjs --output-dir runs/rea-session
```

Wait for `ready:true`. Enter one JSON task per line, replacing the APK path with your absolute path:

```json
{"file":"package","name":"inspect_android_package","args":{"path":"/absolute/path/to/apks/base.apk","detail":"summary"}}
{"file":"class-search","name":"search_android_classes","args":{"path":"/absolute/path/to/apks/base.apk","query":"RealtimeClientManager"}}
{"file":"class-members","name":"inspect_android_class","args":{"path":"/absolute/path/to/apks/base.apk","class_name":"com.instagram.realtimeclient.RealtimeClientManager"}}
{"quit":true}
```

Use `inspect_android_method` with `path`, `class_name`, `method_name` and an explicit `overload_index` when ambiguous. Use `trace_android_references` for incoming static references. Obtain exact selectors from that APK's class inventory; names from our version may have changed. The helper records tool schemas and captures in your ignored run directory and refuses to overwrite existing capture names. It does not launch the app. Native, packed JavaScript, reflection and server-driven paths remain separate investigation work.

## 6. Regenerate selected public reports

The historical trace generators accept both original structured REA envelopes and the sanitized normalized export:

```sh
python3 reels-trace/build_report.py
python3 visibility/build_trace.py
python3 build_report.py
python3 api/helper-scan/rank.py
```

These commands rewrite selected reference reports/indexes. Run them in a separate checkout if you want to preserve the exact published prose. They document the reference artifact, not your newly analyzed version. Missing raw operation/parameter metadata is recorded as omitted rather than invented. The baseline report does not require an omitted device-permission snapshot.

Helper ranking reads `route-method-calls.json.gz` when the uncompressed file is absent. To regenerate its input instead, run `api/helper-scan/scan.py` in a workspace with an APK and catalog first. This helper prioritization is version-specific and is separate from the main extraction pipeline; see PORTING.md.

## Troubleshooting and limits

- **No APK/profile mismatch:** use your own snapshot and `--routes-only`, or select a profile validated for its exact SHA-256. Do not disable the hash check.
- **Unknown methods:** an expected result before tracing the request builders; route names do not determine HTTP verbs.
- **Zero/low coverage with a new profile:** inspect its selectors, decoder errors and request construction. No errors does not establish complete coverage.
- **Missing Node modules:** run `npm ci --ignore-scripts --prefix api`; a browser-login launch additionally needs Chrome.
- **JADX startup failure:** run `doctor.py --android`, verify the full JDK and JAR digest, and confirm your MCP client allows a long enough tool timeout. The capture helper reports child exits/timeouts.
- **Older string-index hashes:** the new index writer uses deterministic gzip headers. Its compressed corpus digest can differ from the historical timestamped gzip even when the indexed records and method/path results agree. Compare the recorded inputs, decoded coverage and operation landmarks; use each run’s own output hashes.
- **Different reports or hashes:** exact inputs, tool versions, profile, and local code changes matter. Original evidence IDs are historical; new decompilation observations can receive new IDs.
- **No sources for native/packed paths:** this pipeline covers standard `classes*.dex` members only. It is not a recovery of the entire client or any backend source.

Publisher signatures are not verified by the archive pipeline. A matching digest identifies the analyzed artifact, not its publisher. Keep observations, inferred semantics, and successful live tests distinct. No API replay or credentials are required for the offline workflow.
