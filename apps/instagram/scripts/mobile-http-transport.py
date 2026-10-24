#!/usr/bin/env python3
"""One allowlisted mobile HTTP/2 request from stdin; no login, retries or disk state."""
import base64
import http.client
import json
import logging
import sys
from urllib.parse import urlsplit

MAX_BODY = 10 * 1024 * 1024
MAX_RESPONSE = 32 * 1024 * 1024


def validate_request(value):
    url = urlsplit(value['url'])
    if url.scheme != 'https' or url.hostname != 'i.instagram.com' or url.port not in (None, 443) or url.username or url.password:
        raise ValueError('unsupported destination')
    if value['method'] not in {'GET','HEAD','POST','PUT','PATCH','DELETE','OPTIONS'}:
        raise ValueError('unsupported method')
    headers = value['headers']
    if not isinstance(headers, dict) or any(not isinstance(k,str) or not isinstance(v,str) or '\r' in k+v or '\n' in k+v for k,v in headers.items()):
        raise ValueError('invalid headers')
    if any(k.lower() in {'host','connection','content-length','transfer-encoding'} for k in headers):
        raise ValueError('transport-managed header')
    body = base64.b64decode(value.get('body',''),validate=True)
    if len(body) > MAX_BODY:
        raise ValueError('request size limit')
    if value['method'] in {'GET','HEAD'} and body:
        raise ValueError('read request body')
    return body


def main():
    logging.disable(logging.CRITICAL)
    value = json.loads(sys.stdin.buffer.read(15 * 1024 * 1024))
    body = validate_request(value)
    import requests
    from instagrapi.transports import create_curl_h2_adapter
    with requests.Session() as session:
        session.trust_env = False
        session.headers.clear()
        session.mount('https://',create_curl_h2_adapter())  # No retries; TLS certificate verification stays enabled.
        with session.request(value['method'],value['url'],headers=value['headers'],data=body or None,
                             allow_redirects=False,timeout=(10,25),stream=True) as response:
            chunks=[]
            size=0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > MAX_RESPONSE:
                    raise ValueError('response size limit')
                chunks.append(chunk)
            # requests decodes the body: do not report the original wire encoding/length.
            headers = {k:v for k,v in response.headers.items() if k.lower() not in {'content-encoding','content-length','transfer-encoding'}}
            print(json.dumps({'status':response.status_code,'headers':headers,'body':base64.b64encode(b''.join(chunks)).decode()}))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps({'error':'Mobile HTTP transport failed.'}))
        raise SystemExit(1) from None
