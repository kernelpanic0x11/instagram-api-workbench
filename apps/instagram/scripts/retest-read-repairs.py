#!/usr/bin/env python3
"""Retest only reviewed, statically justified GET corrections; retain types only."""
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
CORRECTIONS = [
    ('/notifications/get_notification_settings/', {'enable_ig_new_settings': 'false'}),
    ('/business/account/get_suggested_hashtags/', {'used_hashtags': ''}),
    ('/map/search_null_state/', {'signed_body': 'SIGNATURE.{}'}),
]


def main():
    output = ROOT / 'api/read-repair-results.json'
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
        for path, query in CORRECTIONS:
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
    main()
