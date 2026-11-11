#!/usr/bin/env python3
"""Enable user-CA trust gates in the inspected Instagram 454 primary DEX.

The patch is intentionally version-locked. It changes two move-result values to
constant true: the Java user-certificate verifier gate and the MNS/Tigon sandbox
certificate gate. Any byte mismatch is a hard failure.
"""
import argparse
import hashlib
import struct
import sys
import zipfile
import zlib
from pathlib import Path


DEX_SITES = (
    (0x54FAE0, bytes.fromhex("0a06"), bytes.fromhex("1216"), "user certificate gate"),
    (0x54FC12, bytes.fromhex("0a01"), bytes.fromhex("1211"), "MNS sandbox certificate gate"),
    # MNSDGWNetworkStackConfig constructor: replace move/from16 v0,v42 with
    # const/4 v0,true + nop before the trustSandboxCertificates field write.
    (0x823D8E, bytes.fromhex("02002a00"), bytes.fromhex("12100000"), "active DGW certificate gate"),
)


class PatchError(ValueError):
    pass


def patch_dex(original, sites=None):
    data = bytearray(original)
    if len(data) < 32 or data[:4] != b"dex\n":
        raise PatchError("classes.dex has no DEX header")
    sites = DEX_SITES if sites is None else sites
    for offset, expected, replacement, label in sites:
        actual = bytes(data[offset:offset + len(expected)])
        if actual == replacement:
            raise PatchError(f"{label} is already patched")
        if actual != expected:
            raise PatchError(
                f"{label} mismatch at 0x{offset:x}: expected {expected.hex()}, got {actual.hex()}"
            )
        data[offset:offset + len(expected)] = replacement

    # DEX signature covers bytes 32..EOF; checksum covers bytes 12..EOF.
    data[12:32] = hashlib.sha1(data[32:]).digest()
    struct.pack_into("<I", data, 8, zlib.adler32(data[12:]) & 0xFFFFFFFF)
    return bytes(data)


def patch_apk(source, destination):
    if source.resolve() == destination.resolve():
        raise PatchError("refusing to overwrite the input APK")
    if destination.exists():
        raise PatchError(f"refusing to overwrite existing output: {destination}")
    try:
        with zipfile.ZipFile(source) as apk:
            dex = patch_dex(apk.read("classes.dex"))
            with zipfile.ZipFile(destination, "w", allowZip64=True) as output:
                for entry in apk.infolist():
                    if entry.filename.upper().startswith("META-INF/"):
                        continue
                    output.writestr(entry, dex if entry.filename == "classes.dex" else apk.read(entry))
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_apk", type=Path)
    parser.add_argument("output_apk", type=Path)
    args = parser.parse_args()
    try:
        patch_apk(args.input_apk, args.output_apk)
    except (OSError, KeyError, zipfile.BadZipFile, PatchError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(args.output_apk)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
