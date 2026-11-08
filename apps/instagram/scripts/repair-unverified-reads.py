#!/usr/bin/env python3
"""Retest finite APK-backed corrections; keep session context and response values in memory."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

APP = Path(__file__).resolve().parents[1]
OUTPUT = APP / 'api/context-read-repair-results.json'


def load_module(name, filename):
    definition = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    return module


reads = load_module('read_validation', 'validate-read-endpoints.py')
auth = load_module('local_auth_paths', 'connect-instagrapi.py')

# Each variant is a new, bounded client construction. Earlier attempts remain
# in their original result files; a variant may run at most once in this file.
PLAN = json.loads((APP / 'api/context-read-repair-plan.json').read_text())
CORRECTIONS = PLAN['corrections']
ACTIVE_APP_PROFILE = None  # Set only by an isolated, account-verified profile harness.


def verified_account(state):
    verification = state.get('verification') or {}
    if not state.get('connected') or state.get('profile') != 'android' or not verification.get('verified'):
        raise ValueError('Verified local Android session required')
    account = verification.get('account') or {}
    if not str(account.get('id', '')).isdecimal():
        raise ValueError('Verified account identity unavailable')
    return account


def saved_installation_context(account, settings_file=None):
    """Read existing SDK identifiers without constructing a client or refreshing login."""
    settings_file = settings_file or auth.default_session_file()
    if settings_file.is_symlink() or settings_file.stat().st_mode & 0o077:
        raise ValueError('Session settings require private permissions')
    settings = json.loads(settings_file.read_text())
    identity = str((settings.get('authorization_data') or {}).get('ds_user_id') or
                   (settings.get('cookies') or {}).get('ds_user_id') or '')
    if not identity or identity != str(account['id']):
        raise ValueError('Saved session differs from verified account')
    identifiers = settings.get('uuids') or {}
    result = {}
    for source, key in [('saved-installation-uuid', 'uuid'), ('saved-phone-uuid', 'phone_id')]:
        value = identifiers.get(key)
        if not isinstance(value, str) or str(uuid.UUID(value)) != value.lower():
            raise ValueError('Saved installation context unavailable')
        result[source] = value
    return result


def resolve_query(query, context):
    resolved = {}
    for key, value in query.items():
        if isinstance(value, dict):
            if set(value) != {'source'} or value['source'] not in context:
                raise ValueError('Required request context unavailable')
            value = context[value['source']]
        if not isinstance(value, str) or len(value) > 2048 or '\r' in value or '\n' in value:
            raise ValueError('Invalid request context')
        resolved[key] = value
    return resolved


def validate_correction(target, spec, review):
    path = target['path']
    if target.get('appProfile') and target['appProfile'] != ACTIVE_APP_PROFILE:
        raise ValueError('Correction requires its isolated verified app profile')
    if review['source_apk_sha256'] != spec['x-source']['sha256']:
        raise ValueError('Review provenance differs from APK')
    reviewed = next((item for item in review['operations'] if item['path'] == path), None)
    if not reviewed or path in reads.BLOCKED_READ_ROUTES or not re.fullmatch(r'/[A-Za-z0-9_/-]+/', path):
        raise ValueError('Only previously reviewed safe reads may execute')
    operation = spec['paths'].get(path, {}).get('get')
    if not operation or not set(target['query']) <= set(reviewed['fields']):
        raise ValueError('Query is outside recovered GET fields')
    return operation


def failure_diagnostics(value, allowed_fields):
    """Classify a small vocabulary in memory; never return any server string."""
    if not isinstance(value, dict) or value.get('status') != 'fail':
        return {}
    message = value.get('message')
    if not isinstance(message, str):
        return {'failureCategory': 'unclassified'}
    normalized = message.strip().lower()
    exact_categories = {
        'invalid parameters': 'invalid-parameters', 'invalid parameter': 'invalid-parameters',
        'not found': 'not-found', 'not authorized': 'not-authorized',
        'not eligible': 'not-eligible', 'unsupported request': 'unsupported-request',
        'not implemented': 'not-implemented', 'not supported': 'not-supported',
        'not acceptable': 'not-acceptable', 'not signed': 'signature-required',
        'not logged in': 'authentication-required', 'not logged in.': 'authentication-required',
        'not authenticated': 'authentication-required', 'not allowed': 'not-allowed',
        'not permitted': 'not-permitted',
        'unexpected error occurred': 'generic-server-error',
        'something went wrong': 'generic-server-error',
        'something went wrong. please try again later.': 'generic-server-error',
        'oops, an error occurred.': 'generic-server-error',
        'user not found': 'user-not-found', 'media not found': 'media-not-found',
        '': 'empty-message',
    }
    result = {'failureCategory': exact_categories.get(normalized, 'unclassified')}
    vocabulary = {'invalid', 'missing', 'required', 'unsupported', 'deprecated', 'eligible',
                  'eligibility', 'permission', 'permissions', 'parameter', 'parameters',
                  'not', 'found', 'available', 'disabled', 'business', 'professional',
                  'account', 'user', 'media', 'product', 'token', 'expired', 'empty',
                  'error', 'internal', 'request', 'something', 'wrong', 'try', 'again',
                  'later', 'csrf', 'signature', 'logged', 'login', 'allowed', 'implemented',
                  'connected', 'authenticated', 'permitted', 'supported', 'enabled', 'authorized',
                  'app', 'method', 'endpoint', 'signed', 'acceptable', 'enough', 'query',
                  'characters', 'short', 'length', 'session', 'matches', 'matching', 'valid'}
    signals = sorted(set(re.findall(r'[a-z_]+', normalized)) & vocabulary)
    if signals:
        result['messageSignals'] = signals
    # This is a lexical observation, not a claim about server requiredness.
    mentioned = sorted(key for key in allowed_fields
                       if re.search(r'(?<![a-z0-9_])' + re.escape(key) + r'(?![a-z0-9_])', normalized))
    if mentioned:
        result['messageMentionsReviewedFields'] = mentioned
    return result


def observe(opener, token, target, operation, query):
    encoded = urllib.parse.urlencode(query)
    url = reads.ORIGIN + '/proxy' + target['path'] + ('?' + encoded if encoded else '')
    request = urllib.request.Request(url, method='GET', headers={'X-Local-Token': token})
    try:
        response = opener.open(request, timeout=35)
    except urllib.error.HTTPError as error:
        response = error
    check = {'path': target['path'], 'method': 'get', 'queryKeys': sorted(query),
             'requestBodySent': False, 'checkedAt': datetime.now(timezone.utc).isoformat(),
             'transport': 'mobile-http2-worker', 'rawResponseSaved': False, 'personalValuesSaved': False}
    with response:
        check.update(httpStatus=response.status, contentType=response.headers.get_content_type())
        body = response.read(1024 * 1024 + 1)
    value = None
    allowed = {'status', 'message', 'error_type'} | {
        field['name'] for field in operation.get('x-recovered-response-fields', [])
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', field['name'])}
    if len(body) > 1024 * 1024:
        check['bodyKind'] = 'size-limit-exceeded'
    else:
        try:
            value = json.loads(body)
            check.update(reads.shape_metadata(value, allowed))
            reviewed_fields = set((operation.get('x-remaining-read-review') or {}).get('fields', {}))
            check.update(failure_diagnostics(value, set(query) | reviewed_fields))
        except (ValueError, UnicodeError):
            check['bodyKind'] = 'non-json'
    check['outcome'] = 'observed-success' if check['httpStatus'] == 200 and check.get('instagramStatus') == 'ok' and check['contentType'] == 'application/json' else 'not-verified'
    return check, value, reads.stop_reason(check['httpStatus'], value)


def decimal_identifier(value):
    """Accept only an existing positive numeric ID, never a generated substitute."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    text = str(value)
    return text if text.isdecimal() and 0 < len(text) <= 40 and int(text) > 0 else None


def context_from_own_user(value, account):
    user = value.get('user') if isinstance(value, dict) else None
    if not isinstance(user, dict) or decimal_identifier(user.get('pk', user.get('id'))) != str(account['id']):
        raise ValueError('Context response is not the verified account')
    context = {}
    club = user.get('fan_club_info')
    club_id = decimal_identifier(club.get('fan_club_id')) if isinstance(club, dict) else None
    interop_id = decimal_identifier(user.get('interop_messaging_user_fbid'))
    if club_id:
        context['own-fan-club-id'] = club_id
    if interop_id:
        context['own-interop-user-fbid'] = interop_id
    return context


def context_from_suggestions(value, account):
    module = value.get('suggested_users') if isinstance(value, dict) else None
    suggestions = module.get('suggestions') if isinstance(module, dict) else None
    if not isinstance(suggestions, list):
        return {}
    identifiers = []
    for suggestion in suggestions:
        user = suggestion.get('user') if isinstance(suggestion, dict) else None
        identifier = decimal_identifier(user.get('pk', user.get('id'))) if isinstance(user, dict) else None
        if identifier and identifier != str(account['id']) and identifier not in identifiers:
            identifiers.append(identifier)
        if len(identifiers) == 3:
            break
    return {'suggested-user-chain': ','.join(identifiers)} if identifiers else {}


def context_from_followed_creators(value, _account):
    """Select one real club from the authenticated creator recommendation list."""
    creators = value.get('creators') if isinstance(value, dict) else None
    if not isinstance(creators, list):
        return {}
    for creator in creators:
        club = creator.get('fan_club_info') if isinstance(creator, dict) else None
        identifier = decimal_identifier(club.get('fan_club_id')) if isinstance(club, dict) else None
        if identifier:
            return {'selected-fan-club-id': identifier}
    return {}


def persist(results):
    OUTPUT.write_text(json.dumps(results, indent=2) + '\n')


def load_context(opener, state, account, targets, spec, results):
    sources = {value['source'] for _, target, _ in targets for value in target['query'].values()
               if isinstance(value, dict)}
    context = {'verified-account-id': str(account['id'])}
    if isinstance(account.get('username'), str) and account['username']:
        context['verified-account-username'] = account['username']
    if sources & {'saved-installation-uuid', 'saved-phone-uuid'}:
        context.update(saved_installation_context(account))
    if 'new-request-uuid' in sources:
        context['new-request-uuid'] = str(uuid.uuid4())
    if 'local-timezone-offset' in sources:
        context['local-timezone-offset'] = str(int(datetime.now().astimezone().utcoffset().total_seconds()))
    lookups = []
    if sources & {'own-fan-club-id', 'own-interop-user-fbid'}:
        lookups.append(('/accounts/current_user/', {'edit': 'true'}, context_from_own_user))
    if 'suggested-user-chain' in sources:
        lookups.append(('/friendships/recent_followers/', {}, context_from_suggestions))
    if 'selected-fan-club-id' in sources:
        lookups.append(('/api/v1/fan_club/followed_creators_to_susbcribe_to/', {}, context_from_followed_creators))
    for path, query, extract in lookups:
        operation = spec['paths'][path]['get']
        verified = operation.get('x-live-check')
        if not isinstance(verified, dict) or verified.get('outcome') != 'observed-success' or \
                verified.get('path') != path or verified.get('method') != 'get' or \
                verified.get('httpStatus') != 200 or verified.get('instagramStatus') != 'ok' or \
                verified.get('contentType') != 'application/json' or verified.get('requestBodySent') is not False or \
                verified.get('queryKeys') != sorted(query) or path in reads.BLOCKED_READ_ROUTES:
            raise ValueError('Context lookup requires an already verified safe read')
        try:
            check, value, reason = observe(opener, state['token'], {'path': path}, operation, query)
        except Exception:
            results['stoppedBecause'] = 'context-transport-error'
            persist(results)
            raise ValueError('Context transport stopped') from None
        results.setdefault('contextChecks', []).append(check)
        if reason:
            results['stoppedBecause'] = reason
        persist(results)
        if reason or check['outcome'] != 'observed-success':
            raise ValueError('Context read unavailable; no dependent requests attempted')
        context.update(extract(value, account))
        time.sleep(2)
    return context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', choices=CORRECTIONS, action='append', required=True)
    arguments = parser.parse_args()
    if len(set(arguments.target)) != len(arguments.target) or len(arguments.target) > 5:
        raise ValueError('Choose at most five distinct corrections per batch')
    spec = json.loads((APP / 'api/openapi.json').read_text())
    review = json.loads((APP / 'api/remaining-read-review.json').read_text())
    if PLAN['source_apk_sha256'] != spec['x-source']['sha256']:
        raise ValueError('Correction plan provenance differs from APK')
    targets = [(name, CORRECTIONS[name], validate_correction(CORRECTIONS[name], spec, review)) for name in arguments.target]
    results = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {
        'source_apk_sha256': spec['x-source']['sha256'],
        'scope': 'Finite corrected read variants from the frozen remaining-read review. Private session context and response values stay in memory. No login, callbacks, mutations, pagination or automatic retries.',
        'checks': []}
    if results.get('stoppedBecause') or results['source_apk_sha256'] != spec['x-source']['sha256']:
        raise ValueError('Previous protection stop or changed provenance; no automatic resume')
    completed = {item['correction'] for item in results['checks'] + results.get('skipped', [])}
    targets = [item for item in targets if item[0] not in completed]
    if not targets:
        print(json.dumps({'pending': 0}))
        return
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), reads.RejectRedirects())
    with opener.open(reads.ORIGIN + '/api/status', timeout=5) as response:
        state = json.load(response)
    account = verified_account(state)
    context = load_context(opener, state, account, targets, spec, results)
    requests = []
    for name, target, operation in targets:
        if any(isinstance(value, dict) and value['source'] not in context for value in target['query'].values()):
            results.setdefault('skipped', []).append({'correction': name, 'path': target['path'],
                                                      'reason': 'required-context-unavailable'})
            print(json.dumps({'path': target['path'], 'outcome': 'skipped', 'reason': 'required-context-unavailable'}), flush=True)
            persist(results)
        else:
            requests.append((name, target, operation, resolve_query(target['query'], context)))
    for name, target, operation, query in requests:
        try:
            check, _value, reason = observe(opener, state['token'], target, operation, query)
        except Exception:
            results['stoppedBecause'] = 'transport-error'
            persist(results)
            raise ValueError('Transport stopped; no raw exception saved') from None
        check['correction'] = name
        results['checks'].append(check)
        if reason:
            results['stoppedBecause'] = reason
        persist(results)
        print(json.dumps({'path': check['path'], 'httpStatus': check['httpStatus'], 'outcome': check['outcome'], 'stop': reason}), flush=True)
        if reason:
            break
        time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Read repair stopped; no private exception or response values printed.') from None
