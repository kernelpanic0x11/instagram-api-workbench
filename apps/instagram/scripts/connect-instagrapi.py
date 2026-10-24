#!/usr/bin/env python3
"""Authenticate with instagrapi and connect its session to the local workbench.

No APK or phone is needed. Credentials and session settings never go to stdout.
The optional ignored session file lets instagrapi reuse a validated login.
Upstream provider: https://github.com/subzeroid/instagrapi (MIT).
"""
import argparse
import contextlib
import getpass
import io
import json
import logging
import os
import re
import tempfile
import threading
import sys
import urllib.request
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
LOCAL_ORIGIN = 'http://127.0.0.1:8766'
HEADER_POLICY = json.loads((APP_ROOT / 'api/request-header-policy.json').read_text())
ALLOWED_HEADERS = re.compile(r'^(?:' + '|'.join(re.escape(name) for name in HEADER_POLICY['names']) + '|' + '|'.join(re.escape(prefix) + r'[a-z0-9-]+' for prefix in HEADER_POLICY['prefixes']) + r')$', re.I)


class LoginStopped(Exception):
    """Carry a fixed error category instead of an upstream response or credential."""


def default_session_file():
    if sys.platform == 'darwin':
        directory = Path.home() / 'Library/Application Support'
    elif os.name == 'nt':
        directory = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    else:
        directory = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    return directory / 'mobile-api-workbench/auth/instagram.json'


def read_credentials(file):
    values = {}
    for line in file.read_text().splitlines():
        match = re.fullmatch(r'\s*(?:export\s+)?(IG_USERNAME|IG_PASSWORD)\s*=\s*(.*)', line)
        if not match:
            continue
        key, value = match.groups()
        if value.startswith(('"', "'")):
            if len(value) < 2 or value[-1] != value[0]:
                raise LoginStopped('invalid_secrets_file')
            value = value[1:-1]
        else:
            value = value.strip()
        if key in values:
            raise LoginStopped('duplicate_credential_assignment')
        values[key] = value
    if not values.get('IG_USERNAME') or not values.get('IG_PASSWORD'):
        raise LoginStopped('missing_credentials')
    return values['IG_USERNAME'], values['IG_PASSWORD']


def local_call(route, token=None, payload=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['X-Local-Token'] = token
    request = urllib.request.Request(LOCAL_ORIGIN + route, headers=headers,
                                     data=json.dumps(payload).encode() if payload is not None else None)
    # Never route session credentials through an HTTP_PROXY environment setting.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=35) as response:
        return json.loads(response.read(65536))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        raise LoginStopped('local_redirect_rejected')


def connection_payload(client):
    settings = client.get_settings()
    headers = {key: value for key, value in client.private.headers.items()
               if ALLOWED_HEADERS.fullmatch(key) and isinstance(value, str) and not re.search(r'[\r\n]', value)}
    account_id = str(client.user_id)
    if not account_id.isdecimal() or account_id == '0':
        raise LoginStopped('missing_account_identity')
    bearer = client.authorization
    cookies = settings.get('cookies', {})
    cookie = '; '.join(f'{key}={value}' for key, value in cookies.items()
                       if re.fullmatch(r'[A-Za-z0-9_]+', key) and isinstance(value, str) and not re.search(r'[;\r\n]', value))
    if not bearer and not cookies.get('sessionid'):
        raise LoginStopped('missing_session')
    return {'profile': 'android', 'headers': headers, 'bearer': bearer,
            'cookie': cookie, 'expectedAccountId': account_id}


def save_private_settings(file, settings):
    if file.is_symlink():
        raise LoginStopped('session_symlink_rejected')
    file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix='.session-', dir=file.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            json.dump(settings, output)
            output.write('\n')
        os.replace(temporary, file)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def stop_challenge(*_arguments, **_keywords):
    raise LoginStopped('challenge_requires_manual_resolution')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--secrets-file', type=Path, default=Path.home() / '.secrets')
    parser.add_argument('--session-file', type=Path, default=default_session_file())
    parser.add_argument('--web-mfa', action='store_true', help='Accept a verification code through a local web form')
    arguments = parser.parse_args()
    logging.disable(logging.CRITICAL)
    try:
        from instagrapi import Client
        from instagrapi.exceptions import TwoFactorRequired
    except ImportError:
        raise LoginStopped('install_optional_auth_requirements') from None
    try:
        token = local_call('/api/status')['token']
    except Exception:
        raise LoginStopped('start_local_workbench_first') from None
    username, password = read_credentials(arguments.secrets_file)
    form = None
    if arguments.web_mfa:
        from mfa_form import LocalMfaForm
        form = LocalMfaForm()
        print(json.dumps({'verification_form': form.origin, 'state': 'preparing'}), flush=True)
    try:
        finish_login(Client, TwoFactorRequired, arguments, token, username, password, form)
    except Exception:
        if form:
            form.state = 'stopped'
        raise
    finally:
        password = ''
        if form:
            # Keep the result visible briefly after authentication completes.
            threading.Event().wait(120)
            form.close()


def finish_login(Client, TwoFactorRequired, arguments, token, username, password, form):
    # Suppress upstream diagnostics: failures can embed account or response data.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        client = Client()
        client.challenge_code_handler = stop_challenge
        client.change_password_handler = stop_challenge
        if arguments.session_file.exists():
            if arguments.session_file.is_symlink() or arguments.session_file.stat().st_mode & 0o077:
                raise LoginStopped('session_file_requires_private_permissions')
            client.load_settings(arguments.session_file)
        try:
            accepted = client.login(username, password)
        except TwoFactorRequired:
            # getpass writes to the terminal, not to upstream diagnostic buffers.
            if form:
                code = form.wait_for_code()
            else:
                if not os.isatty(0):
                    raise LoginStopped('two_factor_requires_interactive_terminal') from None
                code = getpass.getpass('Instagram verification code (hidden): ')
            if not re.fullmatch(r'[0-9]{6,8}', code):
                raise LoginStopped('invalid_verification_code')
            accepted = client.login(username, password, verification_code=code)
        finally:
            password = ''
        if not accepted:
            raise LoginStopped('authentication_rejected')
        if str(client.account_info().username).casefold() != username.casefold():
            raise LoginStopped('account_identity_mismatch')
        payload = connection_payload(client)
        save_private_settings(arguments.session_file, client.get_settings())
    local_call('/api/connect', token, payload)
    verification = local_call('/api/verify', token, {})
    if form:
        form.state = 'verified' if verification.get('verified') else 'stopped'
    print(json.dumps({'provider': 'instagrapi', 'state': 'verified' if verification.get('verified') else 'unverified',
                      'session_saved_locally': True, 'browser_used': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        reason = str(error) if isinstance(error, LoginStopped) else 'authentication_or_connection_failed'
        print(json.dumps({'state': 'stopped', 'reason': reason}))
        raise SystemExit(1) from None
