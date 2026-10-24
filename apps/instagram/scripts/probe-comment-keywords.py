#!/usr/bin/env python3
"""Read one fixed endpoint via the connected proxy; retain types, never values."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.request

ORIGIN = 'http://127.0.0.1:8766'


def describe_response(value):
    """Allowlist field names and JSON kinds; discard account keyword contents."""
    kinds = {str: 'string', bool: 'boolean', int: 'integer', float: 'number',
             list: 'array', dict: 'object', type(None): 'null'}
    if not isinstance(value, dict):
        return {'bodyKind': 'non-object'}
    result = {'bodyKind': 'object', 'fields': {}}
    for name in ('status', 'keywords', 'disabled', 'message', 'error_type'):
        if name not in value:
            continue
        item = value[name]
        field = {'type': kinds[type(item)]}
        if name == 'keywords' and isinstance(item, list):
            field['observedItemTypes'] = sorted({kinds[type(element)] for element in item})
            field['empty'] = not item
        result['fields'][name] = field
    if value.get('status') in ('ok', 'fail'):
        result['instagramStatus'] = value['status']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'api/comment-keywords-observation.json')
    parser.add_argument('--endpoint', choices=['comment', 'post'], default='comment')
    args = parser.parse_args()
    route = '/accounts/get_' + args.endpoint + '_filter_keywords/'
    if args.endpoint == 'post' and args.output == Path(__file__).resolve().parents[1] / 'api/comment-keywords-observation.json':
        args.output = args.output.with_name('post-keywords-observation.json')
    try:
        with urllib.request.urlopen(ORIGIN + '/api/status', timeout=5) as response:
            state = json.load(response)
        if not state.get('connected') or state.get('profile') != 'android' or not (state.get('verification') or {}).get('verified'):
            raise SystemExit('A verified local Android session is required. No login attempted.')
        request = urllib.request.Request(ORIGIN + '/proxy' + route, headers={'X-Local-Token': state['token']})
        with urllib.request.urlopen(request, timeout=35) as response:
            result = describe_response(json.loads(response.read(65536)))
            result.update(httpStatus=response.status, contentType=response.headers.get_content_type())
    except (OSError, ValueError):
        raise SystemExit('Read check failed; no raw error or response saved.') from None
    result.update(path=route, method='get', queryKeys=[], requestBodySent=False,
                  checkedAt=datetime.now(timezone.utc).isoformat(), rawResponseSaved=False, personalValuesSaved=False)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
