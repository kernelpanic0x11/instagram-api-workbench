#!/usr/bin/env python3
"""Compare old/new header policies using one saved session; never log in or save values.

Run with the optional instagrapi environment and the isolated proxy on port 8768.
Only current-account verification and the fixed notification-settings GET execute.
"""
import importlib.util
import json
import logging
from pathlib import Path
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    logging.disable(logging.CRITICAL)
    from instagrapi import Client
    adapter = module('adapter', 'connect-instagrapi.py')
    reads = module('reads', 'validate-read-endpoints.py')
    adapter.LOCAL_ORIGIN = 'http://127.0.0.1:8768'
    output = ROOT / 'api/notification-transport-observation.json'
    if output.exists():
        raise SystemExit('Comparison already recorded; no automatic repeat.')
    client = Client()
    client.load_settings(adapter.default_session_file())  # Settings only; no login call.
    payload = adapter.connection_payload(client)
    legacy = re.compile(r'^(accept|content-type|user-agent|x-requested-with|x-csrftoken|x-ig-[a-z0-9-]+|x-fb-[a-z0-9-]+|x-bloks-[a-z0-9-]+|x-mid|ig-intended-user-id|x-pigeon-[a-z0-9-]+)$', re.I)
    legacy_headers = {k:v for k,v in payload['headers'].items() if legacy.fullmatch(k)}
    token = adapter.local_call('/api/status')['token']
    result = {'scope':'Same saved session, same GET URL and parameters, two header policies. No login, raw responses, headers values or account values saved.',
              'checkedAt':datetime.now(timezone.utc).isoformat(),
              'addedHeaderNames':sorted(k.lower() for k in payload['headers'] if k not in legacy_headers), 'checks':[]}
    try:
        for variant, headers in [('legacy-header-policy',legacy_headers),('preserved-session-headers',payload['headers'])]:
            adapter.local_call('/api/connect',token,{**payload,'headers':headers})
            verified = adapter.local_call('/api/verify',token,{})
            if not verified.get('verified'):
                result['stoppedBecause']='account-verification-failed'
                break
            request = urllib.request.Request(adapter.LOCAL_ORIGIN + '/proxy/notifications/get_notification_settings/?enable_ig_new_settings=false',headers={'X-Local-Token':token})
            try:
                response = urllib.request.urlopen(request, timeout=35)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                check={'variant':variant,'httpStatus':response.status,'contentType':response.headers.get_content_type()}
                body=response.read(65537)
            value=None
            try:
                value=json.loads(body) if len(body)<=65536 else None
                check.update(reads.shape_metadata(value,{'status','message','error_type'}))
            except (ValueError,UnicodeError):
                check['bodyKind']='non-json'
                lower=body.lower()
                check['recognizedHtmlCategory']='header-size-error' if b'header' in lower and (b'too large' in lower or b'too long' in lower) else 'generic-bad-request' if b'bad request' in lower else 'unclassified'
            check.update(rawResponseSaved=False,personalValuesSaved=False)
            result['checks'].append(check)
            reason=reads.stop_reason(check['httpStatus'],value)
            if reason:
                result['stoppedBecause']=reason
                break
    finally:
        adapter.local_call('/api/disconnect',token,{})
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError):
        raise SystemExit('Comparison stopped; no raw transport or credential error printed.') from None
