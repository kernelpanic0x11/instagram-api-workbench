"""Privacy, stop conditions and execution allowlist checks; no network calls."""
import importlib.util
from pathlib import Path
import json
import unittest
spec = importlib.util.spec_from_file_location('reads', Path(__file__).with_name('validate-read-endpoints.py'))
reads = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reads)


class ReadValidationTests(unittest.TestCase):
    def test_only_allowlisted_names_and_types_survive(self):
        result = reads.shape_metadata({'status':'ok','user':{'pk':123,'username':'private-fixture'},'unknown-private-key':'private-fixture','items':[{'id':123},'private-fixture'], 'message':'private-fixture'}, {'status','user','items','message'})
        self.assertNotIn('private-fixture', json.dumps(result))
        self.assertNotIn('123', json.dumps(result))
        self.assertEqual(result['arrayItemTypes']['items'], ['object','string'])
        self.assertEqual(result['fieldTypes']['user'], 'object')

    def test_empty_arrays_and_boolean_types_are_not_guessed(self):
        result = reads.shape_metadata({'items':[],'flag':False,'status':'private-fixture'}, {'items','flag'})
        self.assertEqual(result['arrayItemTypes']['items'], [])
        self.assertEqual(result['fieldTypes']['flag'], 'boolean')
        self.assertNotIn('instagramStatus',result)

    def test_rate_limits_expiry_and_challenges_stop(self):
        self.assertEqual(reads.stop_reason(429,{}),'rate-limit')
        self.assertIsNotNone(reads.stop_reason(401,{}))
        self.assertIsNotNone(reads.stop_reason(502,{}))
        for value in ({'message':'challenge_required'},{'challenge':{}},{'spam':True},{'feedback_message':'private-fixture'},{'checkpoint_url':'private-fixture'}):
            self.assertIsNotNone(reads.stop_reason(200,value))
        self.assertIsNone(reads.stop_reason(400,{'message':{'arbitrary':'value'}}))

    def test_plan_rejects_mutations_dynamic_routes_and_parameters(self):
        spec={'paths':{'/read/':{'get':{}}}}
        target={'path':'/read/','method':'get','query':{}}
        self.assertEqual(reads.load_plan({'targets':[target]},spec),[target])
        for item in ({**target,'method':'post'},{**target,'query':{'user_id':'123'}},{**target,'path':'/read/{arg1}/'}):
            with self.assertRaises(ValueError):reads.load_plan({'targets':[item]},spec)
        with self.assertRaises(ValueError):reads.load_plan({'targets':[target,target]},spec)

    def test_transport_retest_skips_verified_reads_and_freezes_its_candidate_set(self):
        targets=[{'path':path} for path in ('/first/','/second/','/third/')]
        baseline={'checks':[{'path':'/first/','outcome':'not-verified'}, {'path':'/second/','outcome':'not-verified'}, {'path':'/third/','outcome':'observed-success'}]}
        selected=reads.retest_targets(targets,baseline,{'/second/','/third/'})
        self.assertEqual(selected,[{'path':'/first/'}])
        # A later Swagger rebuild can now mark first successful; preserve the pass inventory.
        self.assertEqual(reads.retest_targets(targets,baseline,{'/first/','/second/'},['/first/']),selected)
        with self.assertRaises(ValueError):reads.retest_targets(targets,baseline,set(),['/third/'])

    def test_additional_plan_accepts_only_recovered_keys_and_bounded_literal_inputs(self):
        spec={'paths':{'/search/':{'get':{'x-recovered-request-fields':[{'name':'q'},{'name':'count'}]}}}}
        target={'path':'/search/','method':'get','query':{'q':'software','count':'3'}}
        self.assertEqual(reads.load_plan({'targets':[target]},spec,True),[target])
        for query in ({'user_id':'123'},{'q':'bad\r\nvalue'},{'q':'x'*81},{'count':3}):
            with self.assertRaises(ValueError):reads.load_plan({'targets':[{**target,'query':query}]},spec,True)
        with self.assertRaises(ValueError):reads.load_plan({'targets':[target]},spec)

    def test_get_verb_cannot_authorize_change_or_security_routes(self):
        for path in reads.BLOCKED_READ_ROUTES:
            with self.assertRaises(ValueError):
                reads.load_plan({'targets':[{'path':path,'method':'get','query':{}}]}, {'paths':{path:{'get':{}}}})


if __name__ == '__main__':
    unittest.main()
