#!/usr/bin/env python3
"""Execute only reviewed GET corrections; resolve private query values in memory."""
import http.client
import importlib.util
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location('reads', Path(__file__).with_name('validate-read-endpoints.py'))
reads = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(reads)
OUTPUT = ROOT / 'api/remaining-read-results.json'


class RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        raise OSError('Redirect rejected')


def corrected_targets(review, api, evidence, blocked):
    """Fail closed on unreviewed routes, stale evidence, or a non-GET operation."""
    digest = api['x-source']['sha256']
    if review.get('source_apk_sha256') != digest or evidence.get('source_apk_sha256') != digest:
        raise ValueError('APK provenance mismatch')
    operations = review['operations']
    if len(operations) != 37 or len({o['path'] for o in operations}) != 37:
        raise ValueError('Expected the frozen set of 37 reviewed operations')
    targets = []
    for operation in operations:
        path = operation['path']
        if path not in evidence['reviewed_routes'] or not all(c in evidence['methods'] for c in operation['callers']):
            raise ValueError('Missing caller evidence')
        if operation['disposition'] != 'corrected-read':
            if 'correctedQuery' in operation:
                raise ValueError('Deferred route must not have an executable query')
            continue
        if path in blocked or not path.startswith('/') or '?' in path or '#' in path or not api['paths'].get(path, {}).get('get'):
            raise ValueError('Only documented, reviewed, nonblocked GET routes may execute')
        query = operation['correctedQuery']
        if not query or not set(query) <= set(operation['fields']):
            raise ValueError('Query lacks reviewed field evidence')
        targets.append(operation)
    return targets


def resolve_query(query, account):
    """Public literals stay in the plan; account identity and UUID never reach artifacts."""
    result = {}
    for key, value in query.items():
        if isinstance(value, dict):
            source = value.get('source')
            if set(value) != {'source'}:
                raise ValueError('Invalid context source')
            if source == 'verified-account-id':
                value = str(account.get('id', ''))
                if not value.isdecimal() or value == '0':
                    raise ValueError('Verified account ID unavailable')
            elif source == 'verified-account-username':
                value = account.get('username')
                if not isinstance(value, str) or not value:
                    raise ValueError('Verified account username unavailable')
            elif source == 'new-request-uuid':
                value = str(uuid.uuid4())
            else:
                raise ValueError('Unknown context source')
        if not isinstance(value, str) or len(value) > 1024 or '\r' in value or '\n' in value:
            raise ValueError('Invalid query value')
        result[key] = value
    return result


def observe(opener, token, operation, query):
    path = operation['path']
    request = urllib.request.Request(reads.ORIGIN + '/proxy' + path + '?' + urllib.parse.urlencode(query),
                                     method='GET', headers={'X-Local-Token': token})
    try:
        response = opener.open(request, timeout=35)
    except urllib.error.HTTPError as error:
        response = error
    check = {'path': path, 'method': 'get', 'queryKeys': sorted(query), 'requestBodySent': False,
             'checkedAt': datetime.now(timezone.utc).isoformat(), 'transport': 'mobile-http2-worker',
             'rawResponseSaved': False, 'personalValuesSaved': False}
    with response:
        check.update(httpStatus=response.status, contentType=response.headers.get_content_type())
        body = response.read(1024 * 1024 + 1)
    allowed = {'status', 'message', 'error_type'} | {f['name'] for f in operation.get('x-recovered-response-fields', [])}
    value = None
    try:
        value = json.loads(body) if len(body) <= 1024 * 1024 else None
        check.update(reads.shape_metadata(value, allowed))
    except (ValueError, UnicodeError):
        check['bodyKind'] = 'non-json'
    check['outcome'] = 'observed-success' if check['httpStatus'] == 200 and check.get('instagramStatus') == 'ok' and check['contentType'] == 'application/json' else 'not-verified'
    return check, reads.stop_reason(check['httpStatus'], value)


def main():
    api = json.loads((ROOT / 'api/openapi.json').read_text())
    review = json.loads((ROOT / 'api/remaining-read-review.json').read_text())
    evidence = json.loads((ROOT / 'api/bulk-trace/remaining-read-evidence.json').read_text())
    blocked = json.loads((ROOT / 'api/online-read-safety.json').read_text())['blockedRoutes']
    targets = corrected_targets(review, api, evidence, blocked)
    result = json.loads(OUTPUT.read_text()) if OUTPUT.exists() else {
        'source_apk_sha256': api['x-source']['sha256'],
        'scope': 'One attempt per evidence-backed read correction from the frozen 37-operation review. No login, mutations, pagination or automatic retries. Only query keys and allowlisted response types retained.',
        'targetPaths': [t['path'] for t in targets], 'checks': []}
    if result.get('stoppedBecause'):
        raise SystemExit('Protection stop present; no automatic resume.')
    if result['source_apk_sha256'] != review['source_apk_sha256'] or result['targetPaths'] != [t['path'] for t in targets]:
        raise ValueError('Recorded target/provenance mismatch')
    pending = [t for t in targets if not any(c['path'] == t['path'] for c in result['checks'])]
    if not pending:
        print(json.dumps({'pending': 0}))
        return
    # No environment proxy, redirects, login, credentials file or session refresh.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), RejectRedirects())
    with opener.open(reads.ORIGIN + '/api/status', timeout=5) as response:
        state = json.load(response)
    verification = state.get('verification') or {}
    if not state.get('connected') or state.get('profile') != 'android' or not verification.get('verified'):
        raise SystemExit('Verified Android connection required; no login attempted.')
    account = verification.get('account') or {}
    # Resolve every required context before the first online API request.
    requests = [(t, resolve_query(t['correctedQuery'], account)) for t in pending]
    for target, query in requests:
        try:
            check, reason = observe(opener, state['token'], {**api['paths'][target['path']]['get'], 'path': target['path']}, query)
        except (OSError, http.client.HTTPException):
            result['stoppedBecause'] = 'transport-error'
            OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
            raise SystemExit('Transport stopped; no raw exception saved.') from None
        result['checks'].append(check)
        if reason:
            result['stoppedBecause'] = reason
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({'path': check['path'], 'httpStatus': check['httpStatus'], 'outcome': check['outcome'], 'stop': reason}), flush=True)
        if reason:
            return
        time.sleep(2)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Read review stopped; no raw account or transport exception printed.') from None
