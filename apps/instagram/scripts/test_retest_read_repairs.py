"""Keep correction probes confined to the reviewed reads; no network calls."""
import importlib.util
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('repairs', Path(__file__).with_name('retest-read-repairs.py'))
repairs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repairs)


class CorrectionAllowlistTests(unittest.TestCase):
    def test_only_three_reviewed_parameter_corrections_execute(self):
        self.assertEqual(dict(repairs.CORRECTIONS), {
            '/notifications/get_notification_settings/': {'enable_ig_new_settings':'false'},
            '/business/account/get_suggested_hashtags/': {'used_hashtags':''},
            '/map/search_null_state/': {'signed_body':'SIGNATURE.{}'},
        })

    def test_probe_reuses_value_discarding_metadata_function(self):
        result = repairs.reads.shape_metadata({'status':'ok','message':'private-fixture','user':{'pk':123}}, {'status','message'})
        self.assertNotIn('private-fixture',str(result))
        self.assertNotIn('user',result['fieldTypes'])


if __name__ == '__main__':
    unittest.main()
