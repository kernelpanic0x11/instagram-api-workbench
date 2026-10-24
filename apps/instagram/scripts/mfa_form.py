"""One-use MFA input on loopback; codes stay in memory and requests are not logged."""
import hmac
import json
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs


class LocalMfaForm:
    def __init__(self, port=8767):
        self.token = secrets.token_urlsafe(32)
        self.state = 'preparing'
        self.code = None
        self.received = threading.Event()
        self.lock = threading.Lock()
        form = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_arguments):
                pass

            def reply(self, status, content, content_type='text/html; charset=utf-8'):
                data = content.encode()
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Referrer-Policy', 'no-referrer')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'nonce-" + form.token + "'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(data)

            def valid_host(self):
                return self.headers.get('Host') == form.address

            def do_GET(self):
                if not self.valid_host():
                    self.reply(403, 'Use the local form address.')
                elif self.path == '/status':
                    self.reply(200, json.dumps({'state': form.state}), 'application/json')
                elif self.path == '/':
                    self.reply(200, form.page())
                else:
                    self.reply(404, 'Not found')

            def do_POST(self):
                self.connection.settimeout(5)
                if not self.valid_host() or self.headers.get('Origin') != form.origin or self.path != '/code':
                    self.reply(403, 'Request rejected.'); return
                length = self.headers.get('Content-Length', '')
                if not length.isdecimal() or not 0 < int(length) <= 512:
                    self.reply(400, 'Invalid submission.'); return
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/x-www-form-urlencoded':
                    self.reply(400, 'Invalid submission.'); return
                try:
                    fields = parse_qs(self.rfile.read(int(length)).decode('ascii'), max_num_fields=2)
                    token, code = fields.get('token', ['']), fields.get('code', [''])
                    valid = len(token) == len(code) == 1 and hmac.compare_digest(token[0], form.token) and re.fullmatch(r'[0-9]{6,8}', code[0])
                except (ValueError, UnicodeError):
                    valid = False
                if not valid:
                    self.reply(400, 'Enter a valid verification code.'); return
                with form.lock:
                    if form.state != 'waiting':
                        self.reply(409, 'The login is not waiting for a code.'); return
                    form.code = code[0]
                    form.state = 'verifying'
                    form.received.set()
                self.reply(200, 'Code received. Verifying with Instagram.')

        self.server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        self.server.daemon_threads = True
        self.address = f'127.0.0.1:{self.server.server_port}'
        self.origin = 'http://' + self.address
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def page(self):
        return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Instagram verification</title><h1>Instagram verification</h1>
<p>This local form sends your code to the login process. The code is not saved.</p>
<p id="status" role="status">Preparing login…</p>
<form id="mfa" action="/code" method="post">
<input type="hidden" name="token" value="TOKEN">
<label>Verification code <input name="code" type="password" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6,8}" minlength="6" maxlength="8" required></label>
<button id="submit" disabled>Submit code</button></form>
<script nonce="TOKEN">
const form=document.querySelector('form'), status=document.querySelector('#status'), button=document.querySelector('button');
const messages={preparing:'Preparing login… Wait before entering a code.',waiting:'Enter your current Instagram verification code.',verifying:'Code received. Verifying with Instagram…',verified:'Connected and verified. Your session is saved locally.',stopped:'Login stopped. Check the workbench terminal.',expired:'This form has expired. Restart the login command.'};
const timer=setInterval(async()=>{try{const r=await fetch('/status',{cache:'no-store'}),s=await r.json();status.textContent=messages[s.state];button.disabled=s.state!=='waiting';if(['verified','stopped','expired'].includes(s.state))clearInterval(timer);}catch{status.textContent='The local login process has closed. Check the terminal for its result.';button.disabled=true;clearInterval(timer);}},1000);
form.addEventListener('submit',async e=>{e.preventDefault();button.disabled=true;const body=new URLSearchParams(new FormData(form));form.elements.code.value='';try{const r=await fetch('/code',{method:'POST',body});status.textContent=await r.text();}catch{status.textContent='Submission failed. Check the local login process.';}});
</script></html>'''.replace('TOKEN', self.token)

    def wait_for_code(self, timeout=300):
        with self.lock:
            self.state = 'waiting'
        if not self.received.wait(timeout):
            self.state = 'expired'
            raise TimeoutError('verification_form_expired')
        with self.lock:
            code, self.code = self.code, None
        return code

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
