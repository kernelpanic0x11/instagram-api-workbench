"""Offline guards for the reviewed batch; fixtures contain no account values."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

module_spec = importlib.util.spec_from_file_location('remaining', Path(__file__).with_name('retest-remaining-reads.py'))
remaining = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(remaining)


class ReviewedBatchTests(unittest.TestCase):
    def setUp(self):
        root = remaining.ROOT
        self.review = json.loads((root / 'api/remaining-read-review.json').read_text())
        self.api = json.loads((root / 'api/openapi.json').read_text())
        self.evidence = json.loads((root / 'api/bulk-trace/remaining-read-evidence.json').read_text())
        self.blocked = json.loads((root / 'api/online-read-safety.json').read_text())['blockedRoutes']

    def targets(self):
        return remaining.corrected_targets(self.review, self.api, self.evidence, self.blocked)

    def test_complete_frozen_review_and_only_corrected_reads_execute(self):
        targets = self.targets()
        self.assertEqual(len(self.review['operations']), 37)
        self.assertEqual(len(targets), 12)
        self.assertTrue(all(t['disposition'] == 'corrected-read' for t in targets))
        self.assertTrue(all(not t['path'].startswith('/trusted_friend/') for t in targets))

    def test_blocked_routes_and_missing_get_rejected(self):
        target = self.targets()[0]
        with self.assertRaises(ValueError):
            remaining.corrected_targets(self.review, self.api, self.evidence, [target['path']])
        self.api['paths'][target['path']].pop('get')
        with self.assertRaises(ValueError):
            self.targets()

    def test_stale_provenance_and_missing_caller_proof_rejected(self):
        digest = self.review['source_apk_sha256']
        self.review['source_apk_sha256'] = 'different'
        with self.assertRaises(ValueError):
            self.targets()
        self.review['source_apk_sha256'] = digest
        self.evidence['methods'].pop(self.review['operations'][0]['callers'][0])
        with self.assertRaises(ValueError):
            self.targets()

    def test_deferred_queries_and_unreviewed_fields_rejected(self):
        deferred = next(t for t in self.review['operations'] if t['disposition'] != 'corrected-read')
        deferred['correctedQuery'] = {'invented': 'value'}
        with self.assertRaises(ValueError):
            self.targets()
        deferred.pop('correctedQuery')
        self.targets()[0]['correctedQuery']['invented'] = 'value'
        with self.assertRaises(ValueError):
            self.targets()

    def test_private_context_resolves_without_mutating_public_plan(self):
        query = {'user_id': {'source': 'verified-account-id'}, 'session_id': {'source': 'new-request-uuid'}}
        before = copy.deepcopy(query)
        resolved = remaining.resolve_query(query, {'id': '12345'})
        self.assertEqual(resolved['user_id'], '12345')
        self.assertEqual(remaining.uuid.UUID(resolved['session_id']).version, 4)
        self.assertEqual(query, before)
        self.assertNotIn('12345', json.dumps(query))

    def test_missing_context_unknown_source_and_crlf_rejected(self):
        for query in [{'id': {'source': 'verified-account-id'}}, {'x': {'source': 'unknown'}}, {'x': 'a\r\nb'}]:
            with self.assertRaises(ValueError):
                remaining.resolve_query(query, {})

    def test_only_safe_shape_metadata_survives(self):
        value = {'status': 'ok', 'message': 'fixture-private-text', 'items': [{'id': 'private-id'}], 'private-key': 'private-value'}
        metadata = remaining.reads.shape_metadata(value, {'status', 'message', 'items'})
        serialized = json.dumps(metadata)
        for secret in ['fixture-private-text', 'private-id', 'private-key', 'private-value']:
            self.assertNotIn(secret, serialized)

    def test_redirects_rejected_instead_of_forwarding_token(self):
        with self.assertRaises(OSError):
            remaining.RejectRedirects().redirect_request(None, None, 302, '', {}, 'https://example.invalid')


if __name__ == '__main__':
    unittest.main()
