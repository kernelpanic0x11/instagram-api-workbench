"""Synthetic bytecode checks for safe integer-switch key recovery."""
import struct
import unittest
from literal_keys import literal_switch_cases
from extract import scan
import test_extract


class SwitchDex:
    def __init__(self):
        self.d = bytearray(64)
        self.name = 'fixture.dex'
        self.methods = [('LFixture;', 'key', '(I)Ljava/lang/String;')]
        self.strings = ['media_infos']
        struct.pack_into('<HH', self.d, 0, 1, 1)
        struct.pack_into('<Hi', self.d, 16, 0x002b, 10)
        struct.pack_into('<HHH', self.d, 22, 0x001a, 0, 0x0011)
        struct.pack_into('<HHii', self.d, 36, 0x0100, 1, 0x140, 3)

    def u16(self, offset): return struct.unpack_from('<H', self.d, offset)[0]
    def u32(self, offset): return struct.unpack_from('<I', self.d, offset)[0]
    def insns(self, code):
        return ([(0, self.u16(16), self.u16(16)&255, 3, 16),
                 (3, self.u16(22), 0x1a, 2, 22), (5, self.u16(26), 0x11, 1, 26)], {})


class LiteralKeyTests(unittest.TestCase):
    def test_returns_only_literal_case_with_physical_evidence(self):
        cases = literal_switch_cases(SwitchDex(), 0, 0)
        self.assertEqual(cases[0x140]['value'], 'media_infos')
        self.assertEqual(cases[0x140]['proof']['entry_byte_offset'], 44)
        self.assertNotIn(0x141, cases)

    def test_nonstatic_input_prefix_work_and_different_return_register_rejected(self):
        for offset, value in [(2, 2), (16, 0x0012), (26, 0x0111)]:
            dex = SwitchDex()
            struct.pack_into('<H', dex.d, offset, value)
            self.assertEqual(literal_switch_cases(dex, 0, 0), {})

    def test_request_key_follows_const16_index_and_move_result_only(self):
        decoder = ('LX/0021;', 'A00', '(I)Ljava/lang/String;')
        suffix = [0x0113, 0x140, 0x1071, 7, 0x0001, 0x020c, 0x306e, 8, 0x0320, 0x106e, 4, 0]
        value = test_extract.TransportTests.fixture(self, suffix)
        value.methods.extend([decoder, ('LX/04x6;', 'AQE', '(Ljava/lang/String;Ljava/lang/String;)V')])
        result = scan(value, 0, 16, include_request_fields=True, literal_decoders={decoder:{0x140:{'value':'media_infos','proof':{'method':'reviewed'}}}})[0]
        self.assertEqual(result['request_fields'][0]['name'], 'media_infos')
        self.assertEqual(result['request_fields'][0]['evidence']['key_origin']['operation'], 'reviewed-literal-switch-key')
        self.assertIn('request_transport', result)
        # An unknown index must not inherit any default literal or prior key.
        self.assertEqual(scan(value, 0, 16, include_request_fields=True, literal_decoders={decoder:{}})[0]['request_fields'], [])
        # A clobbered key register cannot retain the decoded string.
        value = test_extract.TransportTests.fixture(self, suffix[:6] + [0x0212] + suffix[6:])
        value.methods.extend([decoder, ('LX/04x6;', 'AQE', '(Ljava/lang/String;Ljava/lang/String;)V')])
        self.assertEqual(scan(value, 0, 16, include_request_fields=True, literal_decoders={decoder:{0x140:{'value':'media_infos','proof':{}}}})[0]['request_fields'], [])


if __name__ == '__main__':
    unittest.main()
