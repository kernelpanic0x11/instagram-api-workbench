"""Synthetic DEX annotation and privacy-boundary checks; no APKs required."""
import importlib.util
import struct
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('analyze_apks', Path(__file__).with_name('analyze-apks.py'))
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class AnnotationTests(unittest.TestCase):
    def fixture(self, annotation_type='Lretrofit2/http/GET;', elements=b'\x01\x00\x17\x01'):
        dex = analysis.DexAnnotations.__new__(analysis.DexAnnotations)
        data = bytearray(256)
        struct.pack_into('<II', data, 96, 1, 112)
        struct.pack_into('<I', data, 132, 144)
        struct.pack_into('<IIII', data, 144, 0, 0, 1, 0)
        struct.pack_into('<II', data, 160, 0, 176)
        struct.pack_into('<II', data, 176, 1, 192)
        encoded = b'\x01\x00' + elements  # runtime visibility, annotation type, elements
        data[192:192 + len(encoded)] = encoded
        dex.data = bytes(data)
        dex.types = [annotation_type]
        dex.strings = ['value', '/items/{id}', 'method', 'PATCH', 'path']
        dex.methods = ['Lexample/Api;->getItem()V']
        return dex

    def test_method_and_route_come_from_same_method_annotation(self):
        request, = self.fixture().request_annotations()
        self.assertEqual((request['method'], request['path']), ('GET', '/items/{id}'))
        self.assertEqual(request['annotation_byte_offset'], 192)
        self.assertFalse(request['dynamic_url'])

    def test_non_http_annotation_cannot_assign_a_method(self):
        self.assertEqual(list(self.fixture('Lexample/Telemetry;').request_annotations()), [])

    def test_empty_annotation_is_dynamic_url_not_root_endpoint(self):
        request, = self.fixture(elements=b'\x00').request_annotations()
        self.assertEqual(request['path'], '')
        self.assertTrue(request['dynamic_url'])

    def test_custom_http_verb_uses_explicit_method_and_path_fields(self):
        request, = self.fixture('Lretrofit2/http/HTTP;', b'\x02\x02\x17\x03\x04\x17\x01').request_annotations()
        self.assertEqual((request['method'], request['path']), ('PATCH', '/items/{id}'))

    def test_url_output_excludes_userinfo_query_and_fragment(self):
        result = analysis.url_candidate('https://synthetic:secret@example.test/items?token=fixture#private')
        self.assertEqual(result['host'], 'example.test')
        self.assertEqual(result['path'], '/items')
        self.assertNotIn('secret', str(result))
        self.assertNotIn('fixture', str(result))

    def test_local_path_and_malformed_url_are_not_urls(self):
        self.assertIsNone(analysis.url_candidate('/data/local/example'))
        self.assertIsNone(analysis.url_candidate('https://[invalid'))


if __name__ == '__main__':
    unittest.main()
