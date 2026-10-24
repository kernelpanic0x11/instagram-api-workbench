# Reuse research inputs without a phone

Browsing the workbench and using its optional Instagram authentication adapter
require no APK. Static analysis needs APK inputs, which can be supplied as files
instead of pulled from a phone.

Archive a completed input set once, from the repository root:

```sh
python3 scripts/apk-inputs.py archive instagram --version 451.0.0.53.80
python3 scripts/apk-inputs.py list instagram
```

The archive is persistent user data outside the checkout: on macOS it lives
under `~/Library/Application Support/mobile-api-workbench/apks`; on Linux it
uses `$XDG_DATA_HOME` or `~/.local/share`. Set `APK_ARCHIVE_DIR` to choose another
location. Keep a private backup of that directory for recovery on another machine.
An archive on one computer does not automatically transfer to another user.

After a fresh clone, select the full snapshot ID printed by `list`:

```sh
python3 scripts/apk-inputs.py restore instagram --snapshot FULL_SNAPSHOT_ID
```

The same commands accept `snapchat`, `discord`, `tiktok`, and `roblox`.
`archive --source DIRECTORY` accepts an existing directory of APK files.
Archive and restore check hashes and reject conflicting existing inputs.
The snapshots omit source paths, phone serials, and account storage. APKs and
private acquisition receipts remain excluded from Git. Snapshot hashes verify
local consistency; they do not establish the APK publisher's authenticity.
