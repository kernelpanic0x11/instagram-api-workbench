"""Offline privacy and execution guards for finite context-dependent read repairs."""
import copy
from email.message import Message
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


definition = importlib.util.spec_from_file_location(
    'repair_unverified_reads', Path(__file__).with_name('repair-unverified-reads.py'))
repair = importlib.util.module_from_spec(definition)
definition.loader.exec_module(repair)

ACCOUNT = {'id': '12345', 'username': 'fixture_private_username'}
CURRENT_USER = '/accounts/current_user/'
RECENT_FOLLOWERS = '/friendships/recent_followers/'


def verified_state():
    return {'connected': True, 'profile': 'android', 'token': 'fixture_private_token',
            'verification': {'verified': True, 'account': dict(ACCOUNT)}}


def successful_check(path=CURRENT_USER, query_keys=None):
    return {'path': path, 'method': 'get', 'queryKeys': query_keys or [],
            'requestBodySent': False, 'httpStatus': 200, 'instagramStatus': 'ok',
            'contentType': 'application/json', 'outcome': 'observed-success'}


def lookup_spec():
    return {'paths': {
        CURRENT_USER: {'get': {'x-live-check': successful_check(CURRENT_USER, ['edit'])}},
        RECENT_FOLLOWERS: {'get': {'x-live-check': successful_check(RECENT_FOLLOWERS)}}}}


def context_target(source):
    return ('fixture-variant', {'path': '/fixture/read/', 'query': {'context': {'source': source}}}, {})


class Response(io.BytesIO):
    """An in-memory HTTP response; test openers never contact a service."""

    def __init__(self, value, status=200, content_type='application/json'):
        super().__init__(json.dumps(value).encode())
        self.status = status
        self.headers = Message()
        self.headers['Content-Type'] = content_type


class OwnershipTests(unittest.TestCase):
    def test_only_verified_android_session_supplies_identity(self):
        self.assertEqual(repair.verified_account(verified_state()), ACCOUNT)
        for field, invalid in [('connected', False), ('profile', 'web')]:
            state = verified_state()
            state[field] = invalid
            with self.subTest(field=field), self.assertRaises(ValueError):
                repair.verified_account(state)
        for verification in [{}, {'verified': False, 'account': ACCOUNT},
                             {'verified': True, 'account': {'id': 'not-an-id'}}]:
            state = verified_state()
            state['verification'] = verification
            with self.subTest(verification=verification), self.assertRaises(ValueError):
                repair.verified_account(state)

    def test_current_user_context_requires_the_verified_account(self):
        for user in [{'pk': '54321'}, {'pk': True}, {'pk': '54321', 'id': ACCOUNT['id']}, {}]:
            user.update(fan_club_info={'fan_club_id': '70001'}, interop_messaging_user_fbid='80001')
            with self.subTest(user=user), self.assertRaises(ValueError):
                repair.context_from_own_user({'user': user}, ACCOUNT)

    def test_only_exact_club_and_interop_fields_supply_context(self):
        response = {'user': {'pk': int(ACCOUNT['id']),
                             'fan_club_info': {'fan_club_id': '70001'},
                             'interop_messaging_user_fbid': 80001}}
        before = copy.deepcopy(response)
        self.assertEqual(repair.context_from_own_user(response, ACCOUNT), {
            'own-fan-club-id': '70001', 'own-interop-user-fbid': '80001'})
        self.assertEqual(response, before)
        unrelated = {'user': {'id': ACCOUNT['id'], 'fbid_v2': '80001', 'fbid': '80002',
                              'fan_club_id': '70001', 'fan_club_info': {'id': '70002'}},
                     'interop_messaging_user_fbid': '80003'}
        self.assertEqual(repair.context_from_own_user(unrelated, ACCOUNT), {})

    def test_invalid_identifiers_never_become_request_context(self):
        for invalid in [True, False, None, 0, -1, 1.5, '', '0', '-2', '1.0', ' 7', '7\n', '7' * 41]:
            with self.subTest(value=invalid):
                self.assertIsNone(repair.decimal_identifier(invalid))
                self.assertEqual(repair.context_from_own_user({'user': {
                    'pk': ACCOUNT['id'], 'interop_messaging_user_fbid': invalid,
                    'fan_club_info': {'fan_club_id': invalid}}}, ACCOUNT), {})


class InstallationContextTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.settings_file = self.directory / 'fixture-session.json'
        self.settings = {'authorization_data': {'ds_user_id': ACCOUNT['id']}, 'uuids': {
            'uuid': '11111111-2222-4333-8444-555555555555',
            'phone_id': '66666666-7777-4888-8999-aaaaaaaaaaaa'}}
        self.write_settings()

    def write_settings(self):
        self.settings_file.write_text(json.dumps(self.settings))
        self.settings_file.chmod(0o600)

    def test_reads_only_saved_identifiers_for_matching_owner(self):
        self.settings['password'] = 'fixture_private_password'
        self.settings['authorization_data']['sessionid'] = 'fixture_private_session'
        self.write_settings()
        context = repair.saved_installation_context(ACCOUNT, self.settings_file)
        self.assertEqual(context, {'saved-installation-uuid': self.settings['uuids']['uuid'],
                                   'saved-phone-uuid': self.settings['uuids']['phone_id']})
        self.assertNotIn('fixture_private', json.dumps(context))

    def test_other_account_and_missing_owner_are_rejected(self):
        for owner in ['54321', None]:
            self.settings['authorization_data'] = {'ds_user_id': owner}
            self.write_settings()
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                repair.saved_installation_context(ACCOUNT, self.settings_file)

    def test_cookie_owner_is_accepted_only_when_authorization_owner_is_absent(self):
        self.settings.pop('authorization_data')
        self.settings['cookies'] = {'ds_user_id': ACCOUNT['id']}
        self.write_settings()
        self.assertIn('saved-phone-uuid', repair.saved_installation_context(ACCOUNT, self.settings_file))
        self.settings['authorization_data'] = {'ds_user_id': '54321'}
        self.write_settings()
        with self.assertRaises(ValueError):
            repair.saved_installation_context(ACCOUNT, self.settings_file)

    def test_public_permissions_and_symlinks_are_rejected(self):
        self.settings_file.chmod(0o644)
        with self.assertRaises(ValueError):
            repair.saved_installation_context(ACCOUNT, self.settings_file)
        self.settings_file.chmod(0o600)
        alias = self.directory / 'fixture-link.json'
        alias.symlink_to(self.settings_file)
        with self.assertRaises(ValueError):
            repair.saved_installation_context(ACCOUNT, alias)

    def test_incomplete_or_malformed_saved_uuids_are_rejected(self):
        for invalid in [None, '', 'fixture_private_invalid_uuid', '11111111222243338444555555555555']:
            self.settings['uuids']['phone_id'] = invalid
            self.write_settings()
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                repair.saved_installation_context(ACCOUNT, self.settings_file)


class SuggestedContextTests(unittest.TestCase):
    def test_chain_is_unique_bounded_and_excludes_the_verified_user(self):
        identifiers = [ACCOUNT['id'], True, '20001', '20001', '-1', '20002', '20003', '20004']
        value = {'suggested_users': {'suggestions': [{'user': {'pk': value}} for value in identifiers]}}
        before = copy.deepcopy(value)
        self.assertEqual(repair.context_from_suggestions(value, ACCOUNT), {
            'suggested-user-chain': '20001,20002,20003'})
        self.assertEqual(value, before)

    def test_only_users_nested_under_the_recovered_suggestion_shape_are_used(self):
        for value in [None, [], {'users': [{'pk': '20001'}]},
                      {'suggested_users': [{'user': {'pk': '20001'}}]},
                      {'suggested_users': {'suggestions': [{'pk': '20001'}, None, {'user': False}]}}]:
            with self.subTest(value=value):
                self.assertEqual(repair.context_from_suggestions(value, ACCOUNT), {})
        self.assertEqual(repair.context_from_suggestions({'suggested_users': {
            'suggestions': [{'user': {'id': '20002'}}]}}, ACCOUNT), {'suggested-user-chain': '20002'})


class QueryGuardTests(unittest.TestCase):
    def setUp(self):
        self.target = {'path': '/fixture/read/', 'query': {'context': {'source': 'own-context'}}}
        self.spec = {'x-source': {'sha256': 'fixture-apk'},
                     'paths': {self.target['path']: {'get': {'operationId': 'fixture_read'}}}}
        self.review = {'source_apk_sha256': 'fixture-apk', 'operations': [{
            'path': self.target['path'], 'fields': {'context': 'Recovered field'}}]}

    def test_query_resolution_preserves_the_public_plan(self):
        before = copy.deepcopy(self.target)
        self.assertEqual(repair.resolve_query(self.target['query'], {'own-context': 'fixture_private_value'}),
                         {'context': 'fixture_private_value'})
        self.assertEqual(self.target, before)
        self.assertNotIn('fixture_private_value', json.dumps(self.target))

    def test_unknown_sources_malformed_context_and_header_injection_fail_closed(self):
        for value in [{'source': 'missing'}, {'source': 'own-context', 'fallback': '123'},
                      12, None, 'line\rbreak', 'line\nbreak', 'a' * 2049]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                repair.resolve_query({'context': value}, {})
        with self.assertRaises(ValueError):
            repair.resolve_query(self.target['query'], {'own-context': 123})

    def test_only_matching_apk_review_and_get_fields_are_allowed(self):
        self.assertEqual(repair.validate_correction(self.target, self.spec, self.review)['operationId'], 'fixture_read')
        for mutation in ['provenance', 'unknown-field', 'post-only', 'unreviewed']:
            spec, review, target = copy.deepcopy((self.spec, self.review, self.target))
            if mutation == 'provenance':
                review['source_apk_sha256'] = 'different-apk'
            elif mutation == 'unknown-field':
                target['query']['invented'] = '1'
            elif mutation == 'post-only':
                spec['paths'][target['path']] = {'post': {'operationId': 'fixture_post'}}
            else:
                review['operations'] = []
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                repair.validate_correction(target, spec, review)

    def test_blocked_routes_and_route_escape_syntax_are_rejected(self):
        blocked = next(iter(repair.reads.BLOCKED_READ_ROUTES))
        for path in [blocked, '/fixture/../write/', '/fixture/read/?action=write',
                     '/fixture/%2e%2e/write/', 'https://example.invalid/read/']:
            target = {'path': path, 'query': {}}
            spec = {'x-source': {'sha256': 'fixture-apk'}, 'paths': {path: {'get': {'operationId': 'read'}}}}
            review = {'source_apk_sha256': 'fixture-apk', 'operations': [{'path': path, 'fields': {}}]}
            with self.subTest(path=path), self.assertRaises(ValueError):
                repair.validate_correction(target, spec, review)


class PrivacyDiagnosticsTests(unittest.TestCase):
    def test_only_allowlisted_signals_and_exact_reviewed_field_mentions_survive(self):
        message = 'Missing user_fbid for fixture_private_username token=fixture_private_token id=9876543210'
        result = repair.failure_diagnostics({'status': 'fail', 'message': message}, {'user_fbid', 'id'})
        self.assertEqual(result['failureCategory'], 'unclassified')
        self.assertEqual(result['messageSignals'], ['missing', 'token'])
        self.assertEqual(result['messageMentionsReviewedFields'], ['id', 'user_fbid'])
        for private in ['fixture_private_username', 'fixture_private_token', '9876543210', message]:
            self.assertNotIn(private, json.dumps(result))
        result = repair.failure_diagnostics({'status': 'fail', 'message': 'user_fbid_extra productized'},
                                            {'user_fbid', 'product'})
        self.assertNotIn('messageMentionsReviewedFields', result)

    def test_nonfailure_and_structured_messages_never_copy_server_data(self):
        for value in [None, [], {'status': 'ok', 'message': 'fixture_private'},
                      {'status': 'unexpected', 'message': 'fixture_private'}]:
            self.assertEqual(repair.failure_diagnostics(value, {'message'}), {})
        self.assertEqual(repair.failure_diagnostics({'status': 'fail', 'message': {'private': 'value'}}, {}),
                         {'failureCategory': 'unclassified'})
        self.assertEqual(repair.failure_diagnostics({'status': 'fail', 'message': ' INVALID PARAMETERS '}, {})[
            'failureCategory'], 'invalid-parameters')

    def test_observation_retains_shape_without_query_values_or_response_values(self):
        value = {'status': 'ok', 'user': {'pk': '9876543210', 'username': 'fixture_private_username'},
                 'fixture_private_key': 'fixture_private_value'}
        opener = Mock()
        opener.open.return_value = Response(value)
        check, raw_in_memory, reason = repair.observe(opener, 'fixture_private_token',
            {'path': '/fixture/read/'}, {'x-recovered-response-fields': [{'name': 'user'}]},
            {'user_fbid': '9876543210'})
        self.assertEqual(check['outcome'], 'observed-success')
        self.assertEqual(raw_in_memory, value)
        self.assertIsNone(reason)
        self.assertEqual(check['fieldTypes'], {'status': 'string', 'user': 'object'})
        self.assertEqual(check['queryKeys'], ['user_fbid'])
        self.assertFalse(check['requestBodySent'])
        self.assertFalse(check['rawResponseSaved'])
        for private in ['9876543210', 'fixture_private_username', 'fixture_private_key',
                        'fixture_private_value', 'fixture_private_token']:
            self.assertNotIn(private, json.dumps(check))
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), 'GET')
        self.assertIsNone(request.data)

    def test_observation_reports_protection_stop_without_challenge_details(self):
        opener = Mock()
        opener.open.return_value = Response({'status': 'fail', 'message': 'challenge_required',
                                            'challenge_url': 'fixture_private_challenge'}, 400)
        check, _value, reason = repair.observe(opener, 'fixture_private_token',
                                              {'path': '/fixture/read/'}, {}, {})
        self.assertEqual(reason, 'authentication-or-account-protection')
        self.assertEqual(check['outcome'], 'not-verified')
        self.assertNotIn('fixture_private_challenge', json.dumps(check))


class ContextLookupTests(unittest.TestCase):
    def setUp(self):
        self.observe = Mock()
        self.persist = Mock()
        self.patches = [patch.object(repair, 'observe', self.observe),
                        patch.object(repair, 'persist', self.persist), patch.object(repair.time, 'sleep')]
        for mocked in self.patches:
            mocked.start()
            self.addCleanup(mocked.stop)

    def load(self, targets=None, spec=None, results=None):
        return repair.load_context(object(), verified_state(), ACCOUNT,
            targets if targets is not None else [context_target('own-interop-user-fbid')],
            spec if spec is not None else lookup_spec(), results if results is not None else {})

    def test_shared_current_user_lookup_runs_once_and_owns_both_identifiers(self):
        self.observe.return_value = (successful_check(), {'user': {'pk': ACCOUNT['id'],
            'fan_club_info': {'fan_club_id': '70001'}, 'interop_messaging_user_fbid': '80001'}}, None)
        context = self.load([context_target('own-interop-user-fbid'), context_target('own-fan-club-id')])
        self.assertEqual(context['own-interop-user-fbid'], '80001')
        self.assertEqual(context['own-fan-club-id'], '70001')
        self.observe.assert_called_once()
        self.assertEqual(self.observe.call_args.args[2], {'path': CURRENT_USER})
        self.assertEqual(self.observe.call_args.args[4], {'edit': 'true'})

    def test_missing_or_unsuccessful_prior_read_is_rejected_before_lookup(self):
        previous = successful_check(CURRENT_USER, ['edit'])
        for evidence in [None, {}, {'outcome': 'not-verified'},
                         dict(previous, httpStatus=404), dict(previous, instagramStatus='fail'),
                         dict(previous, path='/fixture/unrelated/'), dict(previous, method='post'),
                         dict(previous, contentType='text/html'), dict(previous, requestBodySent=True),
                         dict(previous, queryKeys=[])]:
            spec = lookup_spec()
            spec['paths'][CURRENT_USER]['get']['x-live-check'] = evidence
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                self.load(spec=spec)
        self.observe.assert_not_called()

    def test_protection_stop_prevents_the_next_context_read(self):
        results = {}
        self.observe.return_value = ({'outcome': 'not-verified'}, {}, 'rate-limit')
        with self.assertRaises(ValueError):
            self.load([context_target('own-interop-user-fbid'), context_target('suggested-user-chain')], results=results)
        self.observe.assert_called_once()
        self.assertEqual(results['stoppedBecause'], 'rate-limit')

    def test_context_transport_errors_persist_only_a_fixed_reason(self):
        results = {}
        self.observe.side_effect = OSError('fixture_private_transport_details')
        with self.assertRaises(ValueError) as failure:
            self.load(results=results)
        self.assertEqual(results['stoppedBecause'], 'context-transport-error')
        self.assertNotIn('fixture_private_transport_details', str(failure.exception))
        self.assertNotIn('fixture_private_transport_details', json.dumps(results))

    def test_another_users_response_never_supplies_the_next_lookup(self):
        self.observe.return_value = (successful_check(), {'user': {
            'pk': '54321', 'interop_messaging_user_fbid': '80001'}}, None)
        with self.assertRaises(ValueError):
            self.load([context_target('own-interop-user-fbid'), context_target('suggested-user-chain')])
        self.observe.assert_called_once()

    def test_static_and_verified_identity_context_do_not_fetch_other_sources(self):
        with patch.object(repair, 'saved_installation_context') as installation:
            context = self.load([context_target('verified-account-username')])
        self.assertEqual(context['verified-account-username'], ACCOUNT['username'])
        self.assertEqual(context['verified-account-id'], ACCOUNT['id'])
        self.observe.assert_not_called()
        installation.assert_not_called()


class BatchGuardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        app = Path(directory.name)
        (app / 'api').mkdir()
        self.output = app / 'api/results.json'
        self.target = {'path': '/fixture/read/', 'query': {'user_fbid': {'source': 'own-interop-user-fbid'}}}
        spec = {'x-source': {'sha256': 'fixture-apk'}, 'paths': {
            self.target['path']: {'get': {'operationId': 'fixture_read'}}}}
        review = {'source_apk_sha256': 'fixture-apk', 'operations': [{
            'path': self.target['path'], 'fields': {'user_fbid': 'Recovered field'}}]}
        (app / 'api/openapi.json').write_text(json.dumps(spec))
        (app / 'api/remaining-read-review.json').write_text(json.dumps(review))
        self.opener = Mock()
        self.opener.open.return_value = Response(verified_state())
        self.observer = Mock()
        self.context = Mock(return_value={})
        self.patches = [patch.object(repair, 'APP', app), patch.object(repair, 'OUTPUT', self.output),
            patch.object(repair, 'PLAN', {'source_apk_sha256': 'fixture-apk'}),
            patch.object(repair, 'CORRECTIONS', {'fixture': self.target}),
            patch.object(repair.urllib.request, 'build_opener', return_value=self.opener),
            patch.object(repair, 'load_context', self.context), patch.object(repair, 'observe', self.observer),
            patch('sys.argv', ['repair-unverified-reads.py', '--target', 'fixture']),
            patch('sys.stdout', new_callable=io.StringIO)]
        for mocked in self.patches:
            mocked.start()
            self.addCleanup(mocked.stop)

    def test_missing_context_is_skipped_and_not_retried_on_resume(self):
        repair.main()
        result = json.loads(self.output.read_text())
        self.assertEqual(result['skipped'], [{'correction': 'fixture', 'path': self.target['path'],
                                              'reason': 'required-context-unavailable'}])
        self.assertEqual(result['checks'], [])
        self.observer.assert_not_called()
        self.opener.open.reset_mock()
        self.context.reset_mock()
        repair.main()
        self.opener.open.assert_not_called()
        self.context.assert_not_called()
        for private in [ACCOUNT['id'], ACCOUNT['username'], 'fixture_private_token']:
            self.assertNotIn(private, self.output.read_text())

    def test_previous_protection_stop_prevents_all_network_access(self):
        self.output.write_text(json.dumps({'source_apk_sha256': 'fixture-apk', 'checks': [],
                                           'stoppedBecause': 'rate-limit'}))
        with self.assertRaises(ValueError):
            repair.main()
        self.opener.open.assert_not_called()
        self.context.assert_not_called()
        self.observer.assert_not_called()

    def test_changed_plan_provenance_prevents_all_network_access(self):
        with patch.object(repair, 'PLAN', {'source_apk_sha256': 'different-apk'}):
            with self.assertRaises(ValueError):
                repair.main()
        self.opener.open.assert_not_called()

    def test_duplicate_variants_are_rejected_before_network_access(self):
        with patch('sys.argv', ['repair-unverified-reads.py', '--target', 'fixture', '--target', 'fixture']):
            with self.assertRaises(ValueError):
                repair.main()
        self.opener.open.assert_not_called()


class SelectedClubContextTests(unittest.TestCase):
    def test_selects_existing_club_without_returning_creator_identity(self):
        payload = {'creators': [{'pk': '9001'}, {'pk': '9002', 'fan_club_info': {'fan_club_id': '7001'}},
                                {'pk': '9003', 'fan_club_info': {'fan_club_id': '7002'}}]}
        self.assertEqual(repair.context_from_followed_creators(payload, {}), {'selected-fan-club-id': '7001'})

    def test_missing_club_cannot_fall_back_to_creator_id(self):
        for payload in [None, {}, {'creators': None}, {'creators': [{'pk': '9001'}]},
                        {'creators': [{'fan_club_info': {'fan_club_id': False}}]}]:
            self.assertEqual(repair.context_from_followed_creators(payload, {}), {})

    def test_profile_specific_variant_cannot_run_on_default_connection(self):
        with patch.object(repair, 'ACTIVE_APP_PROFILE', None):
            with self.assertRaisesRegex(ValueError, 'isolated verified app profile'):
                repair.validate_correction({'path': '/fixture/', 'appProfile': 'pinned-apk'}, {}, {})


if __name__ == '__main__':
    unittest.main()
