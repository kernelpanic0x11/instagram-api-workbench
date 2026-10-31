"""Check deep static traces and APK input binding without account access."""
import copy
import hashlib
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import research_inputs

spec = importlib.util.spec_from_file_location('native_trace', Path(__file__).with_name('trace-native.py'))
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)

fallback_spec = importlib.util.spec_from_file_location(
    'instagram_password_fallback',
    Path(__file__).with_name('validate-instagram-password-fallback.py'))
fallback = importlib.util.module_from_spec(fallback_spec)
fallback_spec.loader.exec_module(fallback)


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


class InstagramPasswordFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.trace_path = cls.root / 'apps/instagram/evidence/login-trace.json'
        cls.trace = json.loads(cls.trace_path.read_text())

    def test_checked_in_trace_matches_reviewed_instruction_fingerprints(self):
        result = fallback.validate_trace(self.trace)
        self.assertTrue(result['instruction_fingerprints_verified'])
        self.assertTrue(result['reviewed_data_flow_anchors_matched'])
        self.assertEqual(result['reviewed_methods'], 8)
        self.assertFalse(result['instagram_tag_constant_verified_from_apk'])

    def test_trace_instruction_tampering_fails_closed(self):
        changed = copy.deepcopy(self.trace)
        method = next(item for item in changed['methods']
                      if item['method'] == fallback.WRAPPER_METHOD)
        method['instructions'][0]['opcode'] = '0xff'
        with self.assertRaises(fallback.EvidenceMismatch):
            fallback.validate_trace(changed)

    def test_missing_reviewed_method_fails_closed(self):
        changed = copy.deepcopy(self.trace)
        changed['methods'] = [item for item in changed['methods']
                              if item['method'] != fallback.LOGIN_METHOD]
        with self.assertRaises(fallback.EvidenceMismatch):
            fallback.validate_trace(changed)

    def test_identity_and_scope_metadata_tampering_fails_closed(self):
        for key, value in {
                'app': 'other', 'version': 'other', 'apk_sha256': '0' * 64,
                'status': 'runtime verified'}.items():
            changed = copy.deepcopy(self.trace)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(fallback.EvidenceMismatch):
                fallback.validate_trace(changed)

    def test_malformed_trace_fails_with_evidence_mismatch(self):
        with self.assertRaises(fallback.EvidenceMismatch):
            fallback.validate_trace({'app': 'instagram', 'methods': [None]})

    def test_both_fallback_models_preserve_one_synthetic_sentinel(self):
        for scenario in ('missing-key', 'encrypt-error'):
            result = fallback.run_scenario(scenario, show_synthetic_field=True)
            self.assertEqual(result['version'], 0)
            self.assertTrue(result['fallback_taken'])
            self.assertEqual(result['sentinel_occurrences'], 1)
            self.assertIn(fallback.SYNTHETIC_SENTINEL,
                          result['pre_dispatch_fields']['enc_password'])
        self.assertFalse(fallback.run_scenario('missing-key')['encryption_attempted'])
        self.assertTrue(fallback.run_scenario('encrypt-error')['encryption_attempted'])

    def test_plaintext_key_state_discards_control_ciphertext(self):
        result = fallback.run_scenario('plaintext-key-state', show_synthetic_field=True)
        self.assertEqual(result['tag'], fallback.TRANSIENT_TAG)
        self.assertEqual(result['version'], 0)
        self.assertTrue(result['encryption_attempted'])
        self.assertTrue(result['plaintext_key_state_taken'])
        self.assertFalse(result['fallback_taken'])
        self.assertEqual(result['sentinel_occurrences'], 1)

    def test_success_control_is_opaque_version_four(self):
        result = fallback.run_scenario('success-control', show_synthetic_field=True)
        self.assertEqual(result['version'], 4)
        self.assertFalse(result['fallback_taken'])
        self.assertNotIn(fallback.SYNTHETIC_SENTINEL,
                         result['pre_dispatch_fields']['enc_password'])

    def test_default_report_redacts_the_fixed_sentinel_and_has_no_dispatch(self):
        result = fallback.run_validation(self.trace)
        rendered = json.dumps(result)
        self.assertNotIn(fallback.SYNTHETIC_SENTINEL, rendered)
        self.assertEqual(result['network_requests'], 0)
        self.assertFalse(result['dispatch_available'])
        self.assertIn('APK bytecode was not executed', result['scope'])
        self.assertTrue(result['model_assumptions'])

    def test_cli_rejects_password_argument_without_echoing_value(self):
        secret = 'should-not-appear-in-output'
        result = subprocess.run(
            [sys.executable, str(fallback.ROOT / 'scripts/validate-instagram-password-fallback.py'),
             '--password', secret], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_cli_report_is_offline_and_sanitized(self):
        result = subprocess.run(
            [sys.executable, str(fallback.ROOT / 'scripts/validate-instagram-password-fallback.py')],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['network_requests'], 0)
        self.assertEqual(report['blocked_external_action_attempts'], 0)
        self.assertFalse(report['dispatch_available'])
        self.assertNotIn(fallback.SYNTHETIC_SENTINEL, result.stdout)

    def test_offline_audit_guard_blocks_socket_creation(self):
        program = (
            "import importlib.util,socket;from pathlib import Path;"
            "p=Path('scripts/validate-instagram-password-fallback.py');"
            "s=importlib.util.spec_from_file_location('fallback_guard',p);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "m.install_offline_audit_guard();socket.socket()")
        result = subprocess.run([sys.executable, '-c', program], cwd=fallback.ROOT,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('OfflineGuardViolation', result.stderr)

    def test_offline_audit_guard_blocks_process_creation(self):
        program = (
            "import importlib.util,os;from pathlib import Path;"
            "p=Path('scripts/validate-instagram-password-fallback.py');"
            "s=importlib.util.spec_from_file_location('fallback_guard',p);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "m.install_offline_audit_guard();os.system('true')")
        result = subprocess.run([sys.executable, '-c', program], cwd=fallback.ROOT,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('OfflineGuardViolation', result.stderr)

    def test_modified_apk_is_rejected_before_trace_extraction(self):
        with tempfile.TemporaryDirectory() as temporary:
            apk = Path(temporary) / 'base.apk'
            apk.write_bytes(b'not the pinned APK')
            result = subprocess.run(
                [sys.executable,
                 str(fallback.ROOT / 'scripts/validate-instagram-password-fallback.py'),
                 '--apk', str(apk)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn(str(apk), result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
