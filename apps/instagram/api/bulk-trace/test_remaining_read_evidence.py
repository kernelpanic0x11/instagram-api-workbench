"""Verify compact switch proofs cannot silently bind the wrong encoded key."""
import importlib.util
import struct
import unittest
from pathlib import Path

module_spec = importlib.util.spec_from_file_location('remaining_evidence', Path(__file__).with_name('trace-remaining-reads.py'))
trace = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(trace)


class FixtureDex:
    def __init__(self):
        self.d = bytearray(64)
        self.strings = ['media_infos']
        # A00(index): packed-switch -> const-string v1, index 0 -> return-object v1.
        struct.pack_into('<Hi', self.d, 16, 0x002b, 10)
        struct.pack_into('<HHH', self.d, 22, 0x011a, 0, 0x0111)
        struct.pack_into('<HHii', self.d, 36, 0x0100, 1, 0x140, 3)

    def u16(self, offset):
        return struct.unpack_from('<H', self.d, offset)[0]

    def u32(self, offset):
        return struct.unpack_from('<I', self.d, offset)[0]

    def insns(self, code):
        return ([(0, self.u16(16), 0x2b, 3, 16),
                 (3, self.u16(22), 0x1a, 2, 22),
                 (5, self.u16(26), 0x11, 1, 26)], {})


class KeyProofTests(unittest.TestCase):
    def test_selected_case_records_exact_edge_and_literal_without_other_strings(self):
        result = trace.switch_case_proof(FixtureDex(), 0, {0x140: 'media_infos'})
        self.assertEqual(result[0]['value'], 'media_infos')
        self.assertEqual(result[0]['entry_byte_offset'], 44)
        self.assertEqual(result[0]['target_code_unit_offset'], 3)

    def test_wrong_literal_missing_index_and_wrong_return_register_rejected(self):
        for mutate, expected in [
            (lambda d: None, {0x140: 'wrong-key'}),
            (lambda d: None, {0x141: 'media_infos'}),
            (lambda d: struct.pack_into('<H', d.d, 26, 0x0211), {0x140: 'media_infos'}),
        ]:
            dex = FixtureDex()
            mutate(dex)
            with self.assertRaises(ValueError):
                trace.switch_case_proof(dex, 0, expected)


if __name__ == '__main__':
    unittest.main()
