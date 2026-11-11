# Public identity and publishing

Use only `kernelpanic0x11` and `328764218+kernelpanic0x11@users.noreply.github.com` for this project's commit author and committer identity. Never inherit the global Git identity without checking it. Do not publish the owner's real name, personal email addresses, alternate handles, identifying local paths, or personal preview URLs.

Before any commit or publication, verify the effective author and committer and inspect source, generated artifacts, configuration URLs, documentation, and the history being pushed. A credential scan alone is insufficient.

Never delete a repository to correct a commit identity. Correct only the affected commits, preserving unrelated work, and verify the replacement identity before pushing.

# Working in this repository

Read README.md, CONTRIBUTING.md and the target app's README before changing code.
Keep app-specific work under apps/<app>/. Instagram agent guidance is in
apps/instagram/AGENTS.md; the separate REA web application is documented in
web/README.md, with additional frontend instructions in web/fe/AGENTS.md.
Use the user's task and the actual code to choose a workflow; no particular
skill suite is required.

## Run the Instagram server

From the repository root, with Node.js 20.11 or later:

```sh
cd apps/instagram/api
node server.mjs
```

Open http://127.0.0.1:8766/; stop with Ctrl+C. Catalog browsing needs no npm
install, APK, device or credentials. For another port use `PORT=8767 node
server.mjs` and open that port. Keep the server bound to loopback. Optional
authentication setup is in apps/instagram/api/AUTHENTICATION.txt; do not log in
or execute live API calls merely to test a UI or documentation change.

## Checks and evidence

Run relevant checks from the repository root:

```sh
npm ci --ignore-scripts --prefix apps/instagram/api
npm run build --prefix apps/instagram/api
npm run validate --prefix apps/instagram/api
npm test --prefix apps/instagram/api
python3 apps/instagram/api/bulk-trace/test_extract.py
python3 apps/instagram/scripts/test_reproduce.py
python3 scripts/check-public.py
```

For documentation-only edits, check commands against their implementations and
check local links; do not regenerate unrelated evidence. Use synthetic fixtures.
Distinguish lexical candidates, static traces, runtime observations and successful
requests. Never infer HTTP methods or complete contracts from route names.
Report the checks actually run and any unverified device behavior.

Never commit APKs, signing keys, authentication state, raw device captures, live
account responses or identifying local paths. Review staged files and all commits
being pushed in addition to running the bounded public artifact scan. Check
`git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT` before committing;
environment variables can override Git configuration. Publish only when requested.
