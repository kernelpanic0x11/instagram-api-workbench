#!/usr/bin/env python3
"""Exercise the adapter's privacy boundary without Instagram or instagrapi."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('auth_adapter', Path(__file__).with_name('connect-instagrapi.py'))
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class AuthAdapterTests(unittest.TestCase):
    def test_credentials_are_data_not_shell_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            secrets = Path(directory) / 'secrets'
            secrets.write_text('export IG_USERNAME="synthetic_user"\nIG_PASSWORD=\'$(never-execute)\'\n')
            self.assertEqual(adapter.read_credentials(secrets), ('synthetic_user', '$(never-execute)'))
            secrets.write_text('IG_USERNAME=one\nIG_USERNAME=two\nIG_PASSWORD=synthetic\n')
            with self.assertRaises(adapter.LoginStopped):
                adapter.read_credentials(secrets)

    def test_only_supported_headers_and_safe_cookies_enter_local_proxy(self):
        client = SimpleNamespace(user_id=123, authorization='Bearer synthetic',
            private=SimpleNamespace(headers={'User-Agent': 'synthetic-agent', 'Host': 'untrusted.invalid',
                                             'X-IG-Device-ID': 'synthetic-device', 'IG-U-RUR': 'synthetic-route', 'X-Meta-Usdid': 'synthetic-integrity', 'Accept-Language': 'en-US', 'X-Mid': 'bad\r\nvalue'}),
            get_settings=lambda: {'cookies': {'sessionid': 'synthetic-session', 'bad': 'injected; value'}})
        payload = adapter.connection_payload(client)
        self.assertEqual(payload['expectedAccountId'], '123')
        self.assertEqual(payload['cookie'], 'sessionid=synthetic-session')
        self.assertEqual(set(payload['headers']), {'User-Agent', 'X-IG-Device-ID', 'IG-U-RUR', 'X-Meta-Usdid', 'Accept-Language'})
        client.user_id = 0
        with self.assertRaises(adapter.LoginStopped):
            adapter.connection_payload(client)

    @unittest.skipIf(os.name == 'nt', 'POSIX permission check')
    def test_saved_session_is_private_and_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'sessions/session.json'
            adapter.save_private_settings(file, {'synthetic': 'session'})
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(file.read_text()), {'synthetic': 'session'})
            link = Path(directory) / 'link.json'
            link.symlink_to(file)
            with self.assertRaises(adapter.LoginStopped):
                adapter.save_private_settings(link, {'overwrite': True})
            self.assertEqual(json.loads(file.read_text()), {'synthetic': 'session'})


if __name__ == '__main__':
    unittest.main()
