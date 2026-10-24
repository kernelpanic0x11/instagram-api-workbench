#!/usr/bin/env python3
"""Run reviewed GET reads in paced batches; save allowlisted shape metadata only.

The checked-in plan is the execution allowlist, not a discovery crawler. No
credentials are read from disk, no request values are invented, and no automatic retries or
pagination are performed. Explicit transport-retest mode retains earlier evidence. A status-ok response verifies one bounded read only.
"""
import argparse
from datetime import datetime, timezone
import http.client
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

APP = Path(__file__).resolve().parents[1]
ORIGIN = 'http://127.0.0.1:8766'
BLOCKED_READ_ROUTES = set(json.loads((APP / 'api/online-read-safety.json').read_text())['blockedRoutes'])
KINDS = {str: 'string', bool: 'boolean', int: 'integer', float: 'number',
         dict: 'object', list: 'array', type(None): 'null'}
STOP_MESSAGES = {'challenge_required', 'checkpoint_required', 'login_required', 'feedback_required', 'Please wait a few minutes before you try again.'}


def shape_metadata(value, allowed_fields):
    """Never save response strings, numeric values, arbitrary keys or array items."""
    result = {'bodyKind': KINDS[type(value)], 'fieldTypes': {}, 'arrayItemTypes': {}}
    if not isinstance(value, dict):
        return result
    for name in sorted(allowed_fields):
        if name not in value:
            continue
        item = value[name]
        result['fieldTypes'][name] = KINDS[type(item)]
        if isinstance(item, list):
            result['arrayItemTypes'][name] = sorted({KINDS[type(element)] for element in item})
    if value.get('status') in ('ok', 'fail'):
        result['instagramStatus'] = value['status']
    return result


def stop_reason(status, value):
    if status == 429:
        return 'rate-limit'
    if status >= 500:
        return 'upstream-or-proxy-unavailable'
    if status == 401:
        return 'authentication-expired-or-required'
    if isinstance(value, dict):
        message = value.get('message')
        if isinstance(message, str) and message in STOP_MESSAGES:
            return 'authentication-or-account-protection'
        if value.get('spam') is True or any(key in value for key in ('challenge', 'checkpoint_url', 'challenge_url', 'feedback_title', 'feedback_message')):
            return 'authentication-or-account-protection'
    return None


def load_plan(plan, spec, allow_recovered_query_fields=False):
    seen = set()
    for target in plan['targets']:
        path = target['path']
        if path in BLOCKED_READ_ROUTES:
            raise ValueError('Route may change account state or trigger a security flow')
        if target['method'] != 'get' or path in seen or 'get' not in spec['paths'].get(path, {}) or not re.fullmatch(r'/[A-Za-z0-9_/-]+/', path):
            raise ValueError('Invalid reviewed GET target')
        if allow_recovered_query_fields:
            recovered = {field['name'] for field in spec['paths'][path]['get'].get('x-recovered-request-fields', [])}
            if not set(target['query']) <= recovered or any(not isinstance(value,str) or len(value)>80 or '\r' in value or '\n' in value for value in target['query'].values()):
                raise ValueError('Query differs from recovered parameter keys or reviewed value bounds')
        elif target['query'] != ({'edit': 'true'} if path == '/accounts/current_user/' else {}):
            raise ValueError('Unexpected query in reviewed target')
        seen.add(path)
    return plan['targets']


def retest_targets(targets, baseline, verified_paths, recorded_paths=None):
    """Freeze this pass's original candidate set even if Swagger is rebuilt midway."""
    failed_paths = {item['path'] for item in baseline['checks'] if item['outcome'] != 'observed-success'}
    selected = failed_paths - verified_paths if recorded_paths is None else set(recorded_paths)
    if not selected <= failed_paths:
        raise ValueError('Retest target was not an original unverified read')
    return [target for target in targets if target['path'] in selected]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=10, choices=range(1, 21))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--online-reviewed-reads', action='store_true', help='Test the separate reviewed online read plan without the 100-read goal cap.')
    mode.add_argument('--additional-reviewed-reads', action='store_true', help='Run the bounded search/list plan until the verified-read goal is reached.')
    mode.add_argument('--retest-mobile-transport', action='store_true', help='Retest previously unverified reviewed reads; preserve original results.')
    args = parser.parse_args()
    spec = json.loads((APP / 'api/openapi.json').read_text())
    query_plan = args.additional_reviewed_reads or args.online_reviewed_reads
    plan_file = 'online-read-plan.json' if args.online_reviewed_reads else 'additional-read-plan.json' if args.additional_reviewed_reads else 'read-validation-plan.json'
    plan = json.loads((APP / 'api' / plan_file).read_text())
    if plan.get('source_apk_sha256', spec['x-source']['sha256']) != spec['x-source']['sha256']:
        raise SystemExit('Reviewed plan provenance differs from the target APK.')
    targets = load_plan(plan, spec, allow_recovered_query_fields=query_plan)
    baseline = json.loads((APP / 'api/read-validation-results.json').read_text()) if args.retest_mobile_transport else None
    verified_paths = {path for path, item in spec['paths'].items() if item.get('get', {}).get('x-live-check')}
    output = APP / 'api/mobile-retest-results.json' if args.retest_mobile_transport else APP / 'api/read-validation-results.json'
    if args.additional_reviewed_reads:
        output = APP / 'api/additional-read-results.json'
    if args.online_reviewed_reads:
        output = APP / 'api/online-read-results.json'
    results = json.loads(output.read_text()) if output.exists() else {
        'source_apk_sha256': spec['x-source']['sha256'],
        'scope': 'Paced authenticated GET observations. Field names allowlisted from static parser evidence; types only. No response values, raw bodies, headers, credentials or personal values saved. Success means one HTTP-200 JSON status-ok response, not a complete contract or all feature permissions.',
        'checks': []}
    if args.retest_mobile_transport:
        targets = retest_targets(targets, baseline, verified_paths, results.get('targetPaths'))
        results['targetPaths'] = [target['path'] for target in targets]
    if results.get('stoppedBecause'):
        raise SystemExit('Previous batch stopped for account/transport protection; no automatic resume.')
    if results['source_apk_sha256'] != spec['x-source']['sha256']:
        raise SystemExit('Input provenance changed; no requests made.')
    try:
        with urllib.request.urlopen(ORIGIN + '/api/status', timeout=5) as response:
            state = json.load(response)
    except (OSError, ValueError):
        raise SystemExit('Local session unavailable; no requests made.') from None
    if not state.get('connected') or state.get('profile') != 'android' or not (state.get('verification') or {}).get('verified'):
        raise SystemExit('Verified local Android connection required; no login attempted.')
    tested = {item['path'] for item in results['checks']}
    pending = [target for target in targets if target['path'] not in tested][:args.limit]
    prior_success = {item['path'] for item in json.loads((APP / 'api/runtime-checks.json').read_text())['checks']}
    successful = verified_paths | prior_success | {item['path'] for item in results['checks'] if item['outcome'] == 'observed-success'}
    for target in pending:
        if not args.retest_mobile_transport and not args.online_reviewed_reads and len(successful) >= plan['goal']:
            print('Verified-read goal reached; no additional requests made.')
            break
        path = target['path']
        operation = spec['paths'][path]['get']
        allowed = {'status', 'message', 'error_type'} | {
            field['name'] for field in operation.get('x-recovered-response-fields', [])
            if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,79}', field['name'])}
        query = urllib.parse.urlencode(target['query'])
        url = ORIGIN + '/proxy' + path + ('?' + query if query else '')
        check = {'path': path, 'method': 'get', 'queryKeys': sorted(target['query']),
                 'requestBodySent': False, 'checkedAt': datetime.now(timezone.utc).isoformat(),
                 'rawResponseSaved': False, 'personalValuesSaved': False}
        if args.retest_mobile_transport or query_plan:
            check['transport'] = 'mobile-http2-worker'
        value = None
        try:
            request = urllib.request.Request(url, headers={'X-Local-Token': state['token']})
            try:
                response = urllib.request.urlopen(request, timeout=35)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                check.update(httpStatus=response.status, contentType=response.headers.get_content_type())
                body = response.read(1024 * 1024 + 1)
            if len(body) > 1024 * 1024:
                check['bodyKind'] = 'size-limit-exceeded'
            else:
                try:
                    value = json.loads(body)
                    check.update(shape_metadata(value, allowed))
                except (ValueError, UnicodeError):
                    check['bodyKind'] = 'non-json'
            reason = stop_reason(check['httpStatus'], value)
        except (OSError, http.client.HTTPException):
            check['transportError'] = True
            reason = 'transport-error'
        check['outcome'] = 'observed-success' if check.get('httpStatus') == 200 and check.get('instagramStatus') == 'ok' and check.get('contentType') == 'application/json' else 'not-verified'
        results['checks'].append(check)
        if check['outcome'] == 'observed-success':
            successful.add(path)
        if reason:
            results['stoppedBecause'] = reason
        output.write_text(json.dumps(results, indent=2) + '\n')
        print(json.dumps({'path': path, 'httpStatus': check.get('httpStatus'), 'outcome': check['outcome'], 'stop': reason}), flush=True)
        if reason:
            break
        time.sleep(2)
    print(json.dumps({'attempted': len(results['checks']), 'observedSuccess': sum(item['outcome'] == 'observed-success' for item in results['checks']), 'remainingCandidates': len(targets) - len(results['checks']), 'stoppedBecause': results.get('stoppedBecause'), 'totalVerified':len(successful)}))


if __name__ == '__main__':
    main()
