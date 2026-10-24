"""Prove publication checks catch staged, renamed and historical secrets."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class PublicGuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(Path(__file__).with_name('check-public.py'), self.root / 'scripts/check-public.py')
        self.git('init', '-q')
        self.git('config', 'user.name', 'kernelpanic0x11')
        self.git('config', 'user.email', '328764218+kernelpanic0x11@users.noreply.github.com')

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, *arguments):
        return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', *arguments], cwd=self.root,
                              check=True, capture_output=True)

    def scan(self, *arguments):
        return subprocess.run([sys.executable, 'scripts/check-public.py', *arguments], cwd=self.root,
                              capture_output=True, text=True)

    def test_staged_secret_is_found_even_after_worktree_cleanup(self):
        file = self.root / 'example.txt'
        secret = 'ghp_' + 'SYNTHETIC' * 4
        file.write_text(secret)
        self.git('add', 'example.txt')
        file.write_text('clean working copy')
        result = self.scan()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('staged credential', result.stdout)
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_renamed_authentication_json_is_rejected(self):
        (self.root / 'innocent.json').write_text('{"authorization_data": {}, "cookies": {}}')
        result = self.scan()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('authentication state', result.stdout)

    def test_force_added_secrets_file_is_rejected(self):
        (self.root / '.gitignore').write_text('.secrets\n')
        (self.root / '.secrets').write_text('synthetic fixture')
        self.git('add', '-f', '.secrets')
        self.assertNotEqual(self.scan().returncode, 0)

    def test_removed_secret_in_history_is_rejected_before_push(self):
        file = self.root / 'example.txt'
        file.write_text('ghp_' + 'SYNTHETIC' * 4)
        self.git('add', 'example.txt')
        self.git('commit', '-qm', 'Synthetic credential fixture')
        file.write_text('clean')
        self.git('add', 'example.txt')
        self.git('commit', '-qm', 'Remove fixture')
        self.assertEqual(self.scan().returncode, 0)
        result = self.scan('--history')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('history credential', result.stdout)


if __name__ == '__main__':
    unittest.main()
