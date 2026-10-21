# Trace a new Instagram version

The published helper names belong to one exact APK. Obfuscation can change classes, fields, method signatures, enum slots and control flow between builds—even when endpoint strings look identical. A mapping profile is a reviewed set of bytecode selectors, not an automatic version converter. This repository's extractor is Instagram-oriented; porting to an unrelated app can also require changing route classification and request-construction analysis.

## 1. Start without method assumptions

Acquire a separate snapshot and run the route-only workflow from [REPRODUCING.md](REPRODUCING.md):

```sh
python3 scripts/reproduce.py --apk-dir apks --output runs/discovery --routes-only --package com.instagram.android --version YOUR_VERSION
```

Read `runs/discovery/api/extraction/catalog.json`. Each candidate preserves its literal string and DEX string index/offset. GraphQL-like names and Bloks identifiers are separate candidates, not HTTP routes. The resulting OpenAPI has no GET/POST operations until you establish methods from code.

Preserve the run's manifest and decoder diagnostics. A newer build can move code into packed/native/JavaScript or server-driven paths outside this DEX scanner; fewer candidates do not prove removed features.

## 2. Find construction sites and trace backwards

Configure REA/JADX as described in the reproduction guide. Inspect the new APK's package, class members and selected methods. Start with stable route literals, readable request models or a feature of interest. Use DEX references to find the containing method; follow the request-builder receiver through its setup, setters, helpers and serialization. Incoming references help identify callers but are not a complete dynamic call graph.

For an offline candidate list with containing-method locations, you can use the discovery workspace's helper scan:

```sh
cd runs/discovery
python3 api/helper-scan/scan.py
python3 api/helper-scan/rank.py
```

`scan.py` records route-string/invoke co-occurrence within methods; it does not associate those calls with the same branch or object. `rank.py` includes **reference-version** builder types/priorities. On a new version inspect raw `route-method-calls.json` first and change the ranking filters only after identifying the new types. An empty priority list is not absence of a request builder.

In REA, obtain `class_name` and `method_name` from the target's own inventory; select an explicit overload index when ambiguous. Use decompiled Java as a reading aid and raw instructions/DEX offsets to resolve duplicated blocks, string lookup helpers or misleading variable names. Save the tool's complete structured evidence in an ignored run directory, including input digest, selector, tool version, representation, warnings and limitations.

## 3. Establish each mapping's semantics

Before assigning a verb, retain evidence for all of the following that you use:

1. The field/setter that stores the route on a request builder.
2. The method setter or factory that configures the HTTP verb.
3. The enum/constants-to-verb mapping at the actual request construction layer. A helper name such as `get` alone is insufficient.
4. Receiver identity: the route and method must configure the same object in the traced basic block. Calls in unrelated branches or to another builder do not establish a pair.
5. Helper behavior: argument positions, return receiver, and whether it mutates or replaces a builder. Shared Java types alone do not establish these semantics.
6. Any later override, dispatch or serialization limits you have not traced. Keep those limits explicit rather than inferring successful execution.

Document each mapping with a source file/REA evidence ID and DEX location in a `profile-review.md` beside your captures. Include at least a positive route/method example plus negative cases with an unrelated receiver, a branch boundary and an unknown call. The repository's eight synthetic scanner tests cover these conservatism rules, but they do not validate a new APK's semantics for you.

## 4. Create and fill a draft profile

```sh
python3 scripts/new-profile.py --apk apks/base.apk --package com.instagram.android --version YOUR_VERSION --output runs/my-profile.json
```

The helper computes the APK's exact SHA-256 and writes a **draft** that the scanner deliberately rejects. It does not copy old obfuscated names into the new profile. Fill in the following from your reviewed evidence:

| Key | Shape and meaning |
| --- | --- |
| `apk_sha256` | Measured lowercase digest of that exact base APK |
| `name`, `package`, `version` | Target labels; do not substitute for hash verification |
| `helpers` | `[{"signature":[class,name,descriptor],"method":"GET" or "POST"}]`; factories with verified method semantics |
| `method_helpers` | Same mapping shape, for verified helpers that set a builder's method |
| `path_helpers` | `[[class,name,descriptor]]`; verified route-setting helpers |
| `enum` | Signature/method entries for static field constants representing HTTP verbs |
| `set_method` | `[class,name,descriptor]` for the method setter |
| `route_field`, `method_field` | `[class,name,type_descriptor]` for the corresponding builder fields |
| `provenance` | Your mapping review/capture references and scope |
| `status` | Change from `draft` to `validated` only after the review above |

DEX class descriptors use the form `Lpackage/Class;`. Method descriptors include argument types and a return type, such as `(Ljava/lang/String;)V`; field descriptors contain only the field type. An enum field in the reference mapping is a `Ljava/lang/Integer;`, not an inferred integer number. See the checked-in profile for the full schema and historical examples, **not selectors to transplant**.

A profile exposes only the construction shapes supported by `api/bulk-trace/extract.py`. If a new client uses a different calling convention, control/dataflow pattern or verb representation, extend `scan()` and add meaningful synthetic regressions. Do not force an incompatible shape into an existing profile field. The current analyzer only maps independently verified GET/POST semantics; other methods stay unresolved.

## 5. Trace, validate and review the new result

```sh
python3 scripts/reproduce.py --apk-dir apks --output runs/new-trace --profile runs/my-profile.json
python3 api/bulk-trace/test_extract.py
python3 scripts/test_reproduce.py
```

The scanner rejects a digest mismatch and verifies that the configured method/field signatures exist in the APK before writing its output. The main workflow refuses to overwrite a previous run. It includes reference manual operations and schemas only when the base matches the historical reference digest. A newly ported profile must not silently inherit those three reference operations or their payload schemas.

Review the run's decoder errors, method/path observations, source locations and receiver evidence before promoting operations. Compare the routes with your independent decompiler samples. Record false positives and missing construction patterns, not only counts. JSON/YAML/OpenAPI validation establishes document structure; it does not establish endpoint availability.

When proposing a contribution, include the new profile, target version/base digest, redacted mapping review and precise evidence, scanner tests if behavior changed, and coverage/unknowns. Do not commit APKs, downloaded engines, live responses or authentication state. Use `python3 scripts/check-public.py` to check publishable files before committing. It is a bounded pattern scan, not proof that a release has no private data.

Live verification is a later, separate step using your own session and explicit requests. It is not required to recover method/path configuration, and static success is not evidence of ranking effects or a reach boost.
