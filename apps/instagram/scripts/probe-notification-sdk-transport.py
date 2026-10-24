#!/usr/bin/env python3
"""One fixed GET over the SDK HTTP adapter, with proxy-equivalent app headers.

Loads saved settings only. Does not use private_request, login, retry loops,
challenge handling or response logging. Retains no account/credential values.
"""
import importlib.util
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    logging.disable(logging.CRITICAL)
    output=ROOT/'api/notification-sdk-transport-observation.json'
    if output.exists():
        raise SystemExit('SDK transport observation already exists; no automatic repeat.')
    from instagrapi import Client
    adapter=load('adapter','connect-instagrapi.py')
    reads=load('reads','validate-read-endpoints.py')
    client=Client(session_retry_total=0)
    client.load_settings(adapter.default_session_file())
    payload=adapter.connection_payload(client)
    headers={k.lower():v for k,v in payload['headers'].items()}
    headers['authorization']=payload['bearer']
    headers['cookie']=payload['cookie']
    client.private.headers.clear()
    client.private.headers.update(headers)
    client.private.cookies.clear()  # Exactly the explicit Cookie header; no jar duplication.
    try:
        response=client.private.get('https://i.instagram.com/api/v1/notifications/get_notification_settings/', params={'enable_ig_new_settings':'false'},allow_redirects=False,timeout=25,stream=True)
        body=bytearray()
        for chunk in response.iter_content(8192):
            body.extend(chunk)
            if len(body)>65536:
                break
        result={'transport':client.private_transport,'httpStatus':response.status_code,'contentType':response.headers.get('Content-Type','').split(';')[0].lower(),'rawResponseSaved':False,'personalValuesSaved':False,'checkedAt':datetime.now(timezone.utc).isoformat(),'applicationHeaders':'Same allowed connection headers plus explicit Authorization and Cookie as temporary proxy; HTTP client manages framing and encoding.'}
        value=None
        try:
            value=json.loads(body) if len(body)<=65536 else None
            result.update(reads.shape_metadata(value,{'status','message','error_type'}))
        except (ValueError,UnicodeError):
            result['bodyKind']='non-json'
        result['stoppedBecause']=reads.stop_reason(response.status_code,value)
        response.close()
    finally:
        client.private.close()
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    try:
        main()
    except Exception:
        raise SystemExit('SDK transport observation failed; no raw exception printed.') from None
