#!/usr/bin/env python3
"""Observe two anonymous GET failures; never read credentials or save responses."""
import argparse
from datetime import datetime, timezone
import http.client
import json
from pathlib import Path

TARGETS = ['/accounts/current_user/', '/accounts/get_comment_filter_keywords/']
PUBLIC_HEADERS = {'User-Agent': 'Instagram 451.0.0.53.80 Android (33/13; 420dpi; 1080x2400; Google; Pixel 6; oriole; arm64-v8a; en_US; 385713116)',
                  'X-IG-App-ID': '567067343352427', 'Accept': 'application/json'}


def probe(path):
    connection = http.client.HTTPSConnection('i.instagram.com', timeout=20)
    try:
        connection.request('GET', '/api/v1' + path, headers=PUBLIC_HEADERS)
        response = connection.getresponse()
        body = response.read(65536)
        content_type = response.getheader('Content-Type', '').split(';')[0].lower()
        result = {'path': path, 'method': 'get', 'httpStatus': response.status,
                  'contentType': content_type, 'credentialsSent': False,
                  'redirectFollowed': False, 'rawResponseSaved': False, 'personalValuesSaved': False,
                  'checkedAt': datetime.now(timezone.utc).isoformat()}
        try:
            value = json.loads(body)
        except (ValueError, UnicodeError):
            value = None
        result['bodyKind'] = 'json-object' if isinstance(value, dict) else 'non-json-or-other'
        if isinstance(value, dict):
            types = {str: 'string', bool: 'boolean', int: 'integer', float: 'number', dict: 'object', list: 'array', type(None): 'null'}
            result['fieldTypes'] = {key: types[type(value[key])] for key in ('status', 'message', 'error_type') if key in value}
            if value.get('status') in ('ok', 'fail'):
                result['instagramStatus'] = value['status']
            result['authenticatedIdentityPresent'] = isinstance(value.get('user'), dict) and bool(value['user'].get('pk'))
            if value.get('message') in ('login_required', 'challenge_required', 'checkpoint_required', 'useragent mismatch'):
                result['recognizedError'] = value['message']
        return result
    finally:
        connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'api/runtime-error-checks.json')
    arguments = parser.parse_args()
    checks = []
    try:
        for path in TARGETS:
            check = probe(path)
            checks.append(check)
            print(json.dumps({'path': path, 'httpStatus': check['httpStatus'], 'bodyKind': check['bodyKind'], 'credentialsSent': False}), flush=True)
            if check['httpStatus'] == 429:
                break
    except (OSError, http.client.HTTPException):
        raise SystemExit('Anonymous read probe stopped: network or transport error. No retry performed.') from None
    arguments.output.write_text(json.dumps({'scope': 'Anonymous read-only probes with a public synthetic client profile. Only allowlisted status enums and field types are retained; no raw responses, cookies, headers or personal values saved.', 'checks': checks}, indent=2) + '\n')
