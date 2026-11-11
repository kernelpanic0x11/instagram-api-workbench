import hashlib
import importlib.util
import struct
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path


SCRIPT = Path(__file__).with_name("patch-instagram-user-ca.py")
SPEC = importlib.util.spec_from_file_location("patch_instagram_user_ca", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def dex_with_site(value=b"\x0a\x01"):
    data = bytearray(128)
    data[:8] = b"dex\n035\0"
    data[64:66] = value
    data[12:32] = hashlib.sha1(data[32:]).digest()
    struct.pack_into("<I", data, 8, zlib.adler32(data[12:]) & 0xFFFFFFFF)
    return bytes(data)


class PatchInstagramUserCaTests(unittest.TestCase):
    def test_patches_exact_instruction_and_repairs_dex_header(self):
        original = dex_with_site()
        patched = MODULE.patch_dex(original, ((64, b"\x0a\x01", b"\x12\x11", "test gate"),))
        self.assertEqual(patched[64:66], b"\x12\x11")
        self.assertEqual(patched[12:32], hashlib.sha1(patched[32:]).digest())
        self.assertEqual(struct.unpack_from("<I", patched, 8)[0], zlib.adler32(patched[12:]) & 0xFFFFFFFF)

    def test_refuses_mismatch_and_already_patched_input(self):
        site = ((64, b"\x0a\x01", b"\x12\x11", "test gate"),)
        with self.assertRaisesRegex(MODULE.PatchError, "mismatch"):
            MODULE.patch_dex(dex_with_site(b"\x00\x00"), site)
        with self.assertRaisesRegex(MODULE.PatchError, "already patched"):
            MODULE.patch_dex(dex_with_site(b"\x12\x11"), site)

    def test_apk_preserves_payload_and_removes_old_signatures(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.apk"
            output = Path(directory) / "output.apk"
            with zipfile.ZipFile(source, "w") as apk:
                apk.writestr("classes.dex", dex_with_site())
                apk.writestr("assets/keep", b"yes")
                apk.writestr("META-INF/OLD.RSA", b"old")
            old_sites = MODULE.DEX_SITES
            MODULE.DEX_SITES = ((64, b"\x0a\x01", b"\x12\x11", "test gate"),)
            try:
                MODULE.patch_apk(source, output)
            finally:
                MODULE.DEX_SITES = old_sites
            with zipfile.ZipFile(output) as apk:
                self.assertEqual(apk.read("assets/keep"), b"yes")
                self.assertNotIn("META-INF/OLD.RSA", apk.namelist())


if __name__ == "__main__":
    unittest.main()
