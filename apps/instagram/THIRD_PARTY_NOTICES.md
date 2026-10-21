# Third-party notices

The MIT license covers original workbench code and analysis scripts authored for this project. It does not relicense third-party software or extracted decompiler output.

- **Swagger UI 5.33.3**: Apache-2.0; see `api/vendor/LICENSE`, `api/vendor/NOTICE`, and the JavaScript bundle license files. Vendored from the pinned `swagger-ui-dist` package.
- **REA**: https://github.com/morluto/rea. Used as an analysis tool; its implementation and downloaded analysis engines are not included.
- **JADX headless MCP 0.7.1**: used through REA for selected method decompilation; the JAR is not included.
- **Instagram Android 451.0.0.53.80**: package names, API identifiers, metadata, selected Java/smali snippets, and normalized method evidence originate from the analyzed application. Rights remain with their respective owners. These are evidence artifacts, not an original-source release or a grant to redistribute Instagram's APK.
- npm development dependencies retain their own licenses, listed in `api/package-lock.json` and installed package metadata.

No Instagram account data, session credentials, APKs, or proprietary native/resource binaries are intentionally included.
