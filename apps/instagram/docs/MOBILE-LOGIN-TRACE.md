# Mobile login evidence

The optional authentication adapter delegates live login to
[instagrapi](https://github.com/subzeroid/instagrapi), an MIT-licensed independent
project. The workbench's static research remains separate from that provider.
Provider behavior is not evidence that every recovered APK path works today.

`evidence/login-trace.json` records selected DEX instructions and byte offsets
for Instagram Android 451.0.0.53.80. The extractor rejects any base APK whose
SHA-256 differs from the pinned input. Reproduce it offline from the repo root:

```sh
python3 scripts/trace-instagram-login.py
```

Confirmed in the pinned instructions:

- `LX/0537;->A06` constructs `accounts/login/` and sets the verified POST enum.
  It adds `enc_password`, `guid`, `adid`, `phone_id`, `jazoest`,
  `login_attempt_count`, and `google_tokens`; optional fields include
  `country_codes`, `sn_result`, `sn_nonce`, and `stop_deletion_token`.
- `LX/0242;->A02` and `A04` decode the `username` and `device_id` keys.
  Their static byte array is sliced and XORed with the argument and `0x25`.
- `LX/0227;->A0c` passes the password to `LX/0hHh;->A00`.
  The wrapper sets envelope version 4 and delegates encryption to
  `com.facebook.cryptopub.CryptoPubNative.encrypt`. Its JNI library name is
  `cryptopub-jni`. The wrapper also contains conditional fallback branches;
  these are not permission to assume a plaintext password is accepted.
- `LX/03pn;->A01`, in `classes.dex` at code-item byte offset 5947672,
  reads `IG-Set-Password-Encryption-Pub-Key` and
  `IG-Set-Password-Encryption-Key-Id`, then calls `LX/0Gie;->A02`.
  That method decodes and stores the key; `A01` reads it back for encryption.
- `LX/0KZd;->A00`, in `classes9.dex` at code-item byte offset 4608484,
  constructs `accounts/two_factor_login/`. The selected instructions preserve
  the verification-method and code/context field construction for review.
- Response handlers reference `IG-Set-Authorization`. A header reference alone
  does not prove that a session belongs to a particular account; the adapter
  checks the authenticated username, and the workbench verifies the numeric ID.

Native encryption is not fully traced here. The APK stores many native
libraries inside `assets/lib/libs.spo`; the DEX JNI boundary does not establish
the native binary's entire algorithm. A local experimental compatibility
client was tested with synthetic encryption data, but its live bootstrap did
not return an encryption key and no password was submitted by that client.
It is not the shipped authentication provider.

No account credentials, two-factor codes, device serials, or runtime response
bodies are included in the published instruction evidence. The APK itself is
excluded from Git.
