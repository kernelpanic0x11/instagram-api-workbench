"""Check ARM64 address decoding and APK input binding without proprietary inputs."""
import hashlib
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import research_inputs

spec = importlib.util.spec_from_file_location('native_trace', Path(__file__).with_name('trace-native.py'))
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeAddressTests(unittest.TestCase):
    def test_backward_adrp_pair_matches_independent_objdump_address(self):
        instructions = struct.pack('<II', 0xf0ff3941, 0x911bf021)
        matches = list(native.direct_address_pairs(instructions, 0x1e8a814, {0x5b56fc: 'fixture'}))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['target_virtual_address'], 0x5b56fc)

    def test_shifted_add_uses_page_units(self):
        instructions = struct.pack('<II', 0x90000001, 0x91400421)
        matches = list(native.direct_address_pairs(instructions, 0x1000, {0x2000: 'fixture'}))
        self.assertEqual(len(matches), 1)

    def test_different_source_register_cannot_establish_reference(self):
        instructions = struct.pack('<II', 0x90000001, 0x91000441)
        self.assertEqual(list(native.direct_address_pairs(instructions, 0x1000, {0x1001: 'fixture'})), [])

    def test_nonadjacent_pairs_are_not_claimed(self):
        instructions = struct.pack('<III', 0x90000001, 0xd503201f, 0x91000421)
        self.assertEqual(list(native.direct_address_pairs(instructions, 0x1000, {0x1001: 'fixture'})), [])

    def test_non_arm64_elf_is_rejected(self):
        header = bytearray(64)
        header[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<H', header, 18, 62)
        with self.assertRaises(ValueError):
            native.Elf64(header)


class InputBindingTests(unittest.TestCase):
    def test_modified_apk_is_rejected_before_extracting_any_member(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = root / 'apps/example'
            (app / 'apks').mkdir(parents=True)
            (app / 'evidence').mkdir()
            (app / 'apks/base.apk').write_bytes(b'modified fixture')
            receipt = {'inputs': [{'name': 'base.apk', 'sha256': hashlib.sha256(b'original fixture').hexdigest()}]}
            (app / 'evidence/static-analysis.json').write_text(json.dumps(receipt))
            with patch.object(research_inputs, 'ROOT', root):
                with self.assertRaises(ValueError):
                    research_inputs.extract_member('example', 'base.apk', 'classes.dex', 'classes.dex')
            self.assertFalse((app / 'runs').exists())


if __name__ == '__main__':
    unittest.main()
