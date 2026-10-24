#!/usr/bin/env python3
"""Retest three APK-reviewed GET corrections; keep account identifiers in memory only."""
import http.client
import importlib.util
import json
from pathlib import Path
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reads', Path(__file__).with_name('validate-read-endpoints.py'))
reads = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reads)
def reviewed_corrections():
    # Loading existing settings is local only: never call login or refresh here.
    import logging
    logging.disable(logging.CRITICAL)
    from instagrapi import Client
    module_spec = importlib.util.spec_from_file_location('adapter', Path(__file__).with_name('connect-instagrapi.py'))
    adapter = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(adapter)
    client = Client()
    client.load_settings(adapter.default_session_file())
    account_id = str(client.user_id)
    if not account_id.isdecimal() or account_id == '0':
        raise SystemExit('Saved account identity unavailable; no login attempted.')
    return [
        ('/dynamic_onboarding/get_direct_empty_state/', {
            'user_id': account_id, 'should_contain_combined_unit': 'true',
            'should_contain_message_unit': 'false',
            'should_contain_pending_follow_request_unit': 'false'}),
        ('/api/v1/fan_club/category_members/', {
            'category': 'most_recent', 'limit': '3',
            'should_include_unconnected': 'false', 'should_include_restricted_countries': 'false'}),
        ('/media/sticker_tray_section/', {'surface': 'STORIES', 'section_name': 'custom_stickers'}),
    ]


def main():
    output = ROOT / 'api/second-read-repair-results.json'
    api = json.loads((ROOT / 'api/openapi.json').read_text())
    result = json.loads(output.read_text()) if output.exists() else {'source_apk_sha256': api['x-source']['sha256'], 'scope': 'Evidence-backed read corrections; query keys and response types only. Original failures retained separately.', 'checks': []}
    if result.get('stoppedBecause'):
        raise SystemExit('Protection stop present; no automatic resume.')
    if result['source_apk_sha256'] != api['x-source']['sha256']:
        raise SystemExit('APK provenance mismatch.')
    try:
        with urllib.request.urlopen(reads.ORIGIN + '/api/status', timeout=5) as response:
            state = json.load(response)
        if not state.get('connected') or state.get('profile') != 'android' or not (state.get('verification') or {}).get('verified'):
            raise SystemExit('Verified Android connection required; no login attempted.')
        for path, query in reviewed_corrections():
            if any(c['path'] == path for c in result['checks']):
                continue
            operation = api['paths'][path]['get']
            allowed = {'status', 'message', 'error_type'} | {f['name'] for f in operation.get('x-recovered-response-fields', [])}
            request = urllib.request.Request(reads.ORIGIN + '/proxy' + path + '?' + urllib.parse.urlencode(query), headers={'X-Local-Token': state['token']})
            check = {'path': path, 'method': 'get', 'queryKeys': sorted(query), 'requestBodySent': False, 'checkedAt': datetime.now(timezone.utc).isoformat(), 'rawResponseSaved': False, 'personalValuesSaved': False}
            try:
                response = urllib.request.urlopen(request, timeout=35)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                check.update(httpStatus=response.status, contentType=response.headers.get_content_type())
                body = response.read(1024 * 1024 + 1)
            value = None
            try:
                value = json.loads(body) if len(body) <= 1024 * 1024 else None
                check.update(reads.shape_metadata(value, allowed))
            except (ValueError, UnicodeError):
                check['bodyKind'] = 'non-json'
            check['outcome'] = 'observed-success' if check['httpStatus'] == 200 and check.get('instagramStatus') == 'ok' and check['contentType'] == 'application/json' else 'not-verified'
            reason = reads.stop_reason(check['httpStatus'], value)
            if reason:
                result['stoppedBecause'] = reason
            result['checks'].append(check)
            output.write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps({'path': path, 'httpStatus': check['httpStatus'], 'outcome': check['outcome'], 'stop': reason}), flush=True)
            if reason:
                return
            time.sleep(2)
    except (OSError, http.client.HTTPException):
        result['stoppedBecause'] = 'transport-error'
        output.write_text(json.dumps(result, indent=2) + '\n')
        raise SystemExit('Read correction stopped; no raw error saved.') from None


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit("Read corrections stopped; no raw account or transport exception printed.") from None
