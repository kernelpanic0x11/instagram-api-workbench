"""Ensure the read probe cannot retain keyword values or arbitrary server fields."""
import importlib.util
import json
from pathlib import Path
import unittest
spec = importlib.util.spec_from_file_location('probe', Path(__file__).with_name('probe-comment-keywords.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ResponseMetadataTests(unittest.TestCase):
    def test_private_values_are_discarded(self):
        result = probe.describe_response({'status': 'ok', 'keywords': ['private-fixture'], 'disabled': 1,
                                         'message': 'private-fixture', 'user': {'username': 'private-fixture'}})
        self.assertNotIn('private-fixture', json.dumps(result))
        self.assertNotIn('user', result['fields'])
        self.assertEqual(result['fields']['keywords']['observedItemTypes'], ['string'])
        self.assertNotIn('value', result['fields']['disabled'])

    def test_empty_array_does_not_claim_item_types(self):
        result = probe.describe_response({'status': 'ok', 'keywords': [], 'disabled': False})
        self.assertEqual(result['fields']['keywords']['observedItemTypes'], [])
        self.assertEqual(result['fields']['disabled']['type'], 'boolean')

    def test_unknown_status_and_non_objects_are_not_saved(self):
        self.assertNotIn('instagramStatus', probe.describe_response({'status': 'private-fixture'}))
        self.assertEqual(probe.describe_response(['private-fixture']), {'bodyKind': 'non-object'})


if __name__ == '__main__':
    unittest.main()
