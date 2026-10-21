# Selected static tracing across the four new apps

This pass advances selected candidates into code-level evidence. It does not provide a complete API reconstruction, authenticated workbench, or runtime verification.

| App | Result | Important limit |
| --- | --- | --- |
| Discord 350.8 Stable | Parsed Hermes v98; retained 50 functions with selected references, including API-base construction and relative-URL prefixing | Parser warns v98 is not formally supported; serialized object literals and full wrapper dataflow remain untraced |
| TikTok 47.1.4 | Traced three route declarations through an obfuscated GET annotation into request-factory method/path fields | No host binding, parameter schema, final dispatch or runtime proof |
| Snapchat 14.28.0.54 | Linked a selected service path to protobuf serialization and a gRPC unary-call site, and found its native JNI bridge | Native implementation, protobuf field meanings and runtime behavior remain untraced |
| Roblox 2.743.1136 | Located selected HTTP/URL constants and ARM64 address references, with independent LLVM excerpts | Address references do not establish request construction or execution |

See each app's README and `evidence/` directory for source offsets, hashes, selected instruction excerpts, findings and next steps. Candidate counts include unused code, SDKs, documentation, telemetry and test URLs.

## Inputs and tools

Use the locally acquired APK sets whose hashes match each app's `evidence/static-analysis.json`. The scripts reject mismatched APKs before extraction. They extract required binary members into ignored `apps/<app>/runs/static-deep/` directories automatically. APKs, complete bytecode and downloaded tools remain excluded from Git.

Python 3.10+ is required. DEX tracing reuses only the existing Instagram instruction decoder; it applies no Instagram request-method mappings. The first discovery pass needs Android SDK `apkanalyzer`; the deeper trace scripts do not need it.

Discord uses external [P1sec/hermes-dec](https://github.com/P1sec/hermes-dec), reviewed at commit `2e796663e1fedb93dca51060797ebf3327b3fedb`. It is AGPL-3.0-or-later software, downloaded separately into the ignored tool directory. Its code is not bundled in this project. Inspect the checkout before using it. This pass accessed its Python modules directly, without installation:

```sh
git clone https://github.com/P1sec/hermes-dec.git tools/hermes-dec
git -C tools/hermes-dec checkout 2e796663e1fedb93dca51060797ebf3327b3fedb
python3 scripts/trace-hermes.py
```

The script rejects a different tool commit. The tool's v98 warning remains material even when selected functions decode without errors; a second implementation or version-matched official disassembler should cross-check the results.

Native tracing uses LLVM `llvm-objdump` / `llvm-nm`. Pass the installed executable or directory explicitly when it differs from the macOS Homebrew default. Tools read local binaries only.

## Reproduce the selected traces

From the repository root:

```sh
python3 scripts/trace-dex-candidates.py tiktok snapchat
python3 scripts/trace-tiktok-request-factory.py
python3 scripts/trace-native.py --objdump /path/to/llvm-objdump
python3 scripts/trace-network-bridges.py --llvm-bin /path/to/llvm/bin
python3 scripts/test_analyze_apks.py
python3 scripts/test_deep_traces.py
python3 scripts/check-public.py
```

The TikTok mapping review is a manually reviewed, APK-bound artifact. `trace-tiktok-request-factory.py` regenerates supporting instruction excerpts, not an automatic verdict that an obfuscated annotation means GET on a new app version. Never carry that mapping onto new inputs without review.

Synthetic tests check instruction-address arithmetic, nonmatching register/adjacency cases, annotation parsing, URL-output privacy boundaries and rejection of modified APK inputs. They do not prove real endpoint availability or validate the entire decompiler.

## Privacy and provenance

No app was launched or instrumented, no API request was sent, and no account storage was read. Reports use package metadata, installed APK bytes, source locations, hashes and selected static code excerpts. No device serials or device installation paths are recorded. Credential and identifying-path pattern checks are bounded checks, not proof of absence of every sensitive value.

Original analysis code is covered by the root license. Third-party tools retain their own licenses; extracted app identifiers and disassembly remain research evidence with rights retained by their respective owners. REA was used for the original Instagram work; this pass does not claim REA decompilation of the four new apps.
