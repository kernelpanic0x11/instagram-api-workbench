# Contributing

Keep observations, inferences, and unknowns distinct. New operations should include DEX offsets or decompiler evidence that ties the HTTP method and route to the same request object. Do not infer methods merely from route names or co-occurrence in a function.

Never commit APKs, downloaded analysis engines, credentials, live account responses, or device identifiers. Use synthetic fixtures in tests. Generic request editors must not be presented as recovered schemas.

Run the validation and test commands in the relevant app README. Record app version/hash and coverage limits for new extraction passes. Changes to signing, credentials, forwarding, or request execution need explicit tests of their failure paths.

For new Instagram versions, work from `apps/instagram/` and follow docs/PORTING.md: start route-only, trace request-builder
semantics, and add an exact-digest validated profile with mapping evidence.
Run python3 scripts/test_reproduce.py as well as the scanner and workbench tests.
Do not transplant old obfuscated selectors or manually traced reference schemas
onto another APK. See docs/REPRODUCING.md for isolated output and tool setup.

Keep app-specific code, evidence, dependencies, and scripts under `apps/<app>/`. New app directories are placeholders until implementation is added. Extract shared tooling only when multiple apps actually need it. Run `python3 scripts/check-public.py` from the repository root.
