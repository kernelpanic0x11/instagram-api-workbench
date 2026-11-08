"""Route discovery must preserve provenance and never cross an unknown call."""
import unittest
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from extract import scan_method_routes, is_route_format_template, scan
import test_extract


class RouteDiscoveryTests(unittest.TestCase):
    def test_baseline_is_deduplicated_and_parameter_values_are_not_exported(self):
        fixture = test_extract.RequestFieldTests.fixture(self, [0x031a, 1, 0x306e, 3, 0x0430])
        baseline = scan_method_routes(fixture, 0, 16)
        expanded = scan_method_routes(fixture, 0, 16, {})
        self.assertEqual(expanded, baseline)
        self.assertEqual(len(expanded), 1)
        self.assertNotIn('request_fields', expanded[0])
        self.assertFalse(expanded[0]['dispatch_verified'])

    def decoded_fixture(self, middle=()):
        # Set POST on v0, load integer 42, resolve a pinned literal route into v2,
        # then assign it to the same builder. The decoder lives in another DEX.
        words = test_extract.PREFIX[:5] + [0x0313, 42, 0x1071, 3, 3, 0x020c]
        fixture = test_extract.Fixture(words + list(middle) + [0x025b, 1, 0x000e])
        decoder = ('LX/0000;', 'A00', '(I)Ljava/lang/String;')
        fixture.methods.append(decoder)
        registry = {decoder: {42: {'value': 'users/decoded/', 'proof': {
            'dex': 'decoder.dex', 'input_index': 42, 'string_index': 99}}}}
        return fixture, registry

    def test_decoded_route_has_cross_dex_literal_provenance(self):
        fixture, registry = self.decoded_fixture()
        self.assertEqual(scan_method_routes(fixture, 0, 16), [])
        record = scan_method_routes(fixture, 0, 16, registry)[0]
        self.assertEqual((record['method'], record['path']), ('POST', '/users/decoded/'))
        proof = record['evidence'][0]['string_origin']['decoder']
        self.assertEqual((proof['dex'], proof['input_index']), ('decoder.dex', 42))
        self.assertFalse(record['dispatch_verified'])

    def test_unknown_builder_call_and_branch_still_stop_decoded_routes(self):
        for boundary in ([0x1071, 2, 0], [0x0138, 2]):
            fixture, registry = self.decoded_fixture(boundary)
            self.assertEqual(scan_method_routes(fixture, 0, 16, registry), [])

    def test_unknown_decoder_index_cannot_invent_a_route(self):
        fixture, registry = self.decoded_fixture()
        registry[next(iter(registry))] = {}
        self.assertEqual(scan_method_routes(fixture, 0, 16, registry), [])

    def test_route_finalizer_discovers_a_route_only_in_reviewed_mode(self):
        fixture = test_extract.TransportTests.fixture(self, [0x021a, 1, 0x2071, 7, 0x0020])
        fixture.strings.append('users/finalized/')
        fixture.methods.append(('LX/0224;', 'A0P', '(LX/04x5;Ljava/lang/String;)LX/02sG;'))
        baseline = scan_method_routes(fixture, 0, 16)
        expanded = scan_method_routes(fixture, 0, 16, {})
        self.assertEqual({r['path'] for r in baseline}, {'/users/example/'})
        self.assertEqual({r['path'] for r in expanded}, {'/users/example/', '/users/finalized/'})
        self.assertTrue(all('request_transport' not in r for r in expanded))

    def formatted_fixture(self, before=(), after=()):
        # The format result is a symbolic route, never a literal parameter key.
        words = list(before) + [0x021a, 1, 0x2071, 3, 0x0042, 0x020c]
        fixture = test_extract.Fixture(words + list(after) + [0x025b, 1, 0x000e])
        fixture.strings.append('users/%s/info/')
        fixture.methods.append(('Ljava/lang/String;', 'format', '(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;'))
        return fixture

    def test_symbolic_route_keeps_template_but_no_format_argument_values(self):
        fixture = self.formatted_fixture(after=test_extract.PREFIX[:5])
        self.assertEqual(scan_method_routes(fixture, 0, 16), [])
        record = scan_method_routes(fixture, 0, 16, {})[0]
        self.assertEqual(record['path'], '/users/%s/info/')
        origin = record['evidence'][0]['string_origin']
        self.assertEqual(origin['operation'], 'symbolic-route-format-template')
        self.assertFalse(origin['argument_values_retained'])
        self.assertFalse(record['dispatch_verified'])

    def test_formatter_invalidates_prior_builder_facts(self):
        fixture = self.formatted_fixture(before=test_extract.PREFIX[:5])
        self.assertEqual(scan_method_routes(fixture, 0, 16, {}), [])

    def test_template_cannot_become_a_literal_request_key(self):
        fixture = self.formatted_fixture(after=test_extract.PREFIX[:5] + [0x051a, 0, 0x055b, 1, 0x306e, 4, 0x0320])
        fixture.methods.append(('LX/04x6;', 'AQE', '(Ljava/lang/String;Ljava/lang/String;)V'))
        self.assertTrue(all(not record['request_fields'] for record in scan(fixture, 0, 16, True, {})))

    def test_unsupported_formatters_and_dynamic_prefixes_are_not_routes(self):
        for template in ('%s/users/', 'users/%f/', 'https://example.test/%s/', 'users/%%s/', 'users/%n/', 'users/literal/'):
            self.assertFalse(is_route_format_template(template), template)
        self.assertTrue(is_route_format_template('users/%1$s/items/%2$d/'))
        fixture = self.formatted_fixture(after=test_extract.PREFIX[:5])
        fixture.methods[3] = ('LUnknown;', 'format', fixture.methods[3][2])
        self.assertEqual(scan_method_routes(fixture, 0, 16, {}), [])

    def test_locale_formatter_uses_second_argument_and_omits_argument_values(self):
        words = [0x051a, 2, 0x1024, 0, 5, 0x040c, 0x021a, 1, 0x3071, 3, 0x0426, 0x020c]
        fixture = test_extract.Fixture(words + test_extract.PREFIX[:5] + [0x025b, 1, 0x000e])
        fixture.strings.extend(['users/%s/info/', 'synthetic-account-context'])
        fixture.methods.append(('Ljava/lang/String;', 'format', '(Ljava/util/Locale;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;'))
        result = scan_method_routes(fixture, 0, 16, {})
        self.assertEqual(result[0]['path'], '/users/%s/info/')
        self.assertNotIn('synthetic-account-context', json.dumps(result))

    def test_reviewed_mode_rejects_another_validated_profile_before_output(self):
        directory = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            apk = root / 'fixture.apk'
            apk.write_bytes(b'foreign fixture')
            profile = json.loads((directory / 'profiles/instagram-451.json').read_text())
            profile['apk_sha256'] = hashlib.sha256(apk.read_bytes()).hexdigest()
            profile_file = root / 'profile.json'
            profile_file.write_text(json.dumps(profile))
            output = root / 'operations.json'
            result = subprocess.run([sys.executable, str(directory / 'extract.py'), '--apk', str(apk),
                '--profile', str(profile_file), '--output', str(output), '--reviewed-contracts'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('pinned reference APK', result.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
