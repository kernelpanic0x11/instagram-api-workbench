#!/usr/bin/env python3
"""Reconnect saved settings without login, then verify four fixed read routes."""
import importlib.util
import json
import logging
from pathlib import Path
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
READS=[('/business/account/get_suggested_hashtags/',{'used_hashtags':''}),('/map/search_null_state/',{'signed_body':'SIGNATURE.{}'}),('/users/get_message_settings_v2/',{}),('/api/v1/accounts/get_embeds_opt_out/',{})]


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    logging.disable(logging.CRITICAL)
    from instagrapi import Client
    adapter=load('adapter','connect-instagrapi.py');reads=load('reads','validate-read-endpoints.py')
    api=json.loads((ROOT/'api/openapi.json').read_text());output=ROOT/'api/transport-validation-results.json';results=json.loads(output.read_text())
    if results.get('stoppedBecause'):raise SystemExit('Protection stop; no automatic resume.')
    client=Client();client.load_settings(adapter.default_session_file())
    token=adapter.local_call('/api/status')['token']
    adapter.local_call('/api/connect',token,adapter.connection_payload(client))
    if not adapter.local_call('/api/verify',token,{}).get('verified'):raise SystemExit('Account verification failed; no additional reads.')
    for path,query in READS:
        if any(c['path']==path for c in results['checks']):continue
        request=urllib.request.Request(adapter.LOCAL_ORIGIN+'/proxy'+path+('?' + urllib.parse.urlencode(query) if query else ''),headers={'X-Local-Token':token})
        try:response=urllib.request.urlopen(request,timeout=35)
        except urllib.error.HTTPError as error:response=error
        with response:
            check={'path':path,'method':'get','queryKeys':sorted(query),'requestBodySent':False,'transport':'mobile-http2-worker','httpStatus':response.status,'contentType':response.headers.get_content_type(),'rawResponseSaved':False,'personalValuesSaved':False,'checkedAt':datetime.now(timezone.utc).isoformat()};body=response.read(1024*1024+1)
        allowed={'status','message','error_type'}|{f['name'] for f in api['paths'][path]['get'].get('x-recovered-response-fields',[])};value=None
        try:value=json.loads(body) if len(body)<=1024*1024 else None;check.update(reads.shape_metadata(value,allowed))
        except (ValueError,UnicodeError):check['bodyKind']='non-json'
        check['outcome']='observed-success' if check['httpStatus']==200 and check.get('instagramStatus')=='ok' and check['contentType']=='application/json' else 'not-verified'
        results['checks'].append(check);reason=reads.stop_reason(check['httpStatus'],value)
        if reason:results['stoppedBecause']=reason
        output.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'path':path,'httpStatus':check['httpStatus'],'outcome':check['outcome'],'stop':reason}),flush=True)
        if reason:break
        time.sleep(2)


if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Read verification failed; no raw account/transport exception printed.') from None
