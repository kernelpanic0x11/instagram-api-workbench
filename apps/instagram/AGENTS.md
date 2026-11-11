# Instagram development and modification

Commands here run from apps/instagram/ unless stated otherwise. Read README.md,
SECURITY.md and ../../CONTRIBUTING.md. Use Python 3.11+ for the analysis scripts.

## Workbench changes

The local Node server and browser UI live in api/. Start with `node api/server.mjs`
and open http://127.0.0.1:8766/. Edit the relevant UI/proxy source there; inspect
api/package.json for build, validation and test commands. Generated OpenAPI
outputs should come from the build and evidence inputs, not manual schema guesses.
The separate web/ application is not this local catalog server.

## Analyze another Instagram version

Follow docs/REPRODUCING.md for tool setup and acquisition from an authorized
device, and docs/PORTING.md for mapping validation. Keep each APK snapshot separate.

```sh
python3 scripts/doctor.py
python3 scripts/reproduce.py --apk-dir apks --output runs/discovery --routes-only --package com.instagram.android --version YOUR_VERSION
```

Use a fresh output directory. The reference catalog describes version
451.0.0.53.80; do not transplant its obfuscated selectors onto a different APK.
Record exact input hashes and validate a new mapping profile before assigning
HTTP operations. Static analysis needs no account login.

## Modify a local APK

These are research helpers, not a complete Android application source tree or a
one-command APK build system. Use your own APKs and keep outputs under ignored
build/ or runs/ directories. Preserve original inputs and record their hashes.

- scripts/patch-debuggable-apk.py edits compiled manifest attributes. It supports
  --clone-package, --app-label, --launcher-class and --no-debuggable; inspect
  `python3 scripts/patch-debuggable-apk.py --help` before selecting options.
  Clone mode changes installation identity while retaining Java component names.
- scripts/EvilLaunchActivity.java contains the custom launcher, profile back stack,
  fire overlay and terminal styling. Artwork is in assets/. The launcher loads
  evil_emblem.png, evil_fire_overlay.png and an optional evil_profile username
  from APK assets; asset packaging must use those exact runtime names. Keep a
  personal evil_profile file out of Git.
- --launcher-class changes manifest references only. Adding the launcher also
  requires compiling Java against a suitable Android SDK, converting classes to
  DEX, and packaging the DEX and assets into the APK. Inspect the target's existing
  DEX members to choose a free name; do not assume a fixed classesN.dex slot.
- scripts/patch-instagram-user-ca.py changes three bytecode sites for the inspected
  version 454 primary DEX and repairs its checksum/signature. It is separate from
  manifest debugging and is not a general certificate-pinning bypass. Verify the
  exact target instructions and input digest first; never disable mismatch checks
  to force it onto another build.

Example manifest-only clone (from apps/instagram/):

```sh
mkdir -p build/local
python3 scripts/patch-debuggable-apk.py --clone-package com.instagram.android.inspect --app-label 'Research Instagram' apks/base.apk build/local/base-unsigned.apk
```

The output is unsigned. Modified APKs need alignment and signing with your own
private test key using Android SDK Build Tools. For split installations, inspect
and patch the complete matching split set as needed and sign every member with
the same key; a changed base alone may not install. Never commit keys, APKs or
signing credentials. This repository does not automate that complete packaging
and installation process. Do not uninstall an existing app or erase its data to
resolve a signature conflict without explicit authorization.

## Verify changes

From the repository root:

```sh
python3 -m unittest discover -s apps/instagram/scripts -p 'test_patch_debuggable_apk.py'
python3 -m unittest discover -s apps/instagram/scripts -p 'test_patch_instagram_user_ca.py'
python3 -m unittest discover -s apps/instagram/scripts -p 'test_evil_launch_activity.py'
python3 scripts/check-public.py
```

These synthetic and source checks do not prove APK installation, animation or
runtime compatibility. With an explicitly authorized device task, use
scripts/verify_evil_back_stack.py after installing the clone: it launches the app,
presses Back, checks foreground activity and reads/clears logcat. It requires an
authorized ADB connection and an unlocked phone. It targets
com.instagram.android.inspect; inspect its constants before testing another clone.
Keep screenshots, logs and account/device identifiers private and report runtime
checks separately from offline test results.
