"""Verify persistent APK snapshots using synthetic ZIP fixtures, without a phone."""
import importlib.util
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('apk_inputs', Path(__file__).with_name('apk-inputs.py'))
inputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inputs)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / 'checkout/apps/instagram/apks'
        self.source.mkdir(parents=True)
        self.archive = self.root / 'persistent'
        for name in ['base.apk', 'split_config.en.apk']:
            with zipfile.ZipFile(self.source / name, 'w') as apk:
                apk.writestr('fixture.txt', 'synthetic APK container fixture')

    def tearDown(self):
        self.temporary.cleanup()

    def save(self):
        return inputs.archive_inputs('instagram', self.source, self.archive, 'synthetic')

    def test_checkout_can_be_removed_and_restored_without_a_device(self):
        manifest = self.save()
        shutil.rmtree(self.root / 'checkout')
        restored = inputs.restore_inputs('instagram', manifest['snapshot'], self.source, self.archive)
        inputs.verify_snapshot(self.source, restored)
        self.assertEqual(len(restored['files']), 2)
        self.assertNotIn(str(self.root), json.dumps(manifest))
        self.assertEqual(self.save()['snapshot'], manifest['snapshot'])

    def test_archive_tampering_is_rejected_before_creating_destination(self):
        manifest = self.save()
        archived = self.archive / 'instagram' / manifest['snapshot'] / 'base.apk'
        archived.write_bytes(b'changed')
        destination = self.root / 'restored'
        with self.assertRaises(ValueError):
            inputs.restore_inputs('instagram', manifest['snapshot'], destination, self.archive)
        self.assertFalse(destination.exists())

    def test_existing_different_inputs_are_never_overwritten(self):
        manifest = self.save()
        original = self.source / 'base.apk'
        original.write_bytes(b'local changed input')
        with self.assertRaises(ValueError):
            inputs.restore_inputs('instagram', manifest['snapshot'], self.source, self.archive)
        self.assertEqual(original.read_bytes(), b'local changed input')

    def test_manifest_cannot_escape_snapshot_directory(self):
        manifest = self.save()
        manifest['files'][0]['name'] = '../base.apk'
        manifest['snapshot'] = inputs.snapshot_id(manifest['files'])
        with self.assertRaises(ValueError):
            inputs.validate_manifest(manifest)

    def test_missing_or_extra_apks_cannot_silently_change_a_receipted_snapshot(self):
        manifest = self.save()
        (self.source / 'acquisition.json').write_text(json.dumps({'package': inputs.PACKAGES['instagram'], 'files': manifest['files']}))
        (self.source / 'split_config.en.apk').unlink()
        with self.assertRaises(ValueError):
            self.save()


if __name__ == '__main__':
    unittest.main()
