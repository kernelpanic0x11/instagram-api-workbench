#!/usr/bin/env python3
"""Provision the approved REA Cognito domain; switch config only after HTTPS is ready."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

root = Path(__file__).resolve().parents[1]
aws = ['aws', '--profile', 'admin', '--region', 'us-east-1', '--no-cli-pager']
def call(*args):
    result = subprocess.run(aws + list(args), check=True, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout.strip() else None

zone = 'Z088611318NWZXC5161YY'
domain = 'auth.re.beehivewebstudio.com'
outputs = call('cloudformation', 'describe-stacks', '--stack-name', 'rea-auth')['Stacks'][0]['Outputs']
pool = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'CognitoUserPoolId')
records = call('route53', 'list-resource-record-sets', '--hosted-zone-id', zone)['ResourceRecordSets']
parent = [r for r in records if r['Name'] == 're.beehivewebstudio.com.' and r['Type'] in ('A', 'CNAME')]
if not parent:
    # AWS requires a resolvable parent. This documented placeholder serves no application.
    batch = {'Comment': 'REA Cognito parent verification; replace when hosting the app', 'Changes': [{'Action': 'CREATE', 'ResourceRecordSet': {'Name': 're.beehivewebstudio.com.', 'Type': 'A', 'TTL': 60, 'ResourceRecords': [{'Value': '198.51.100.1'}]}}]}
    change = call('route53', 'change-resource-record-sets', '--hosted-zone-id', zone, '--change-batch', json.dumps(batch))
    subprocess.run(aws + ['route53', 'wait', 'resource-record-sets-changed', '--id', change['ChangeInfo']['Id']], check=True)
subprocess.run(aws + ['cloudformation', 'deploy', '--stack-name', 'rea-auth-domain', '--template-file', str(root / 'infra/auth-domain-stack.json'), '--parameter-overrides', 'UserPoolId=' + pool, 'HostedZoneId=' + zone, '--no-fail-on-empty-changeset'], check=True)
# Certificate/CloudFront propagation can continue after stack completion. Never disable TLS validation.
for attempt in range(90):
    try:
        with urllib.request.urlopen('https://' + domain + '/.well-known/openid-configuration', timeout=15) as response:
            discovery = json.load(response)
        if discovery['authorization_endpoint'].startswith('https://' + domain + '/'):
            break
    except (OSError, ValueError, KeyError):
        pass
    print('Waiting for custom login HTTPS propagation...', flush=True)
    time.sleep(20)
else:
    raise SystemExit('Domain deployed but HTTPS is not ready. Existing sign-in configuration was preserved; rerun later.')
file = root / 'be/.env'
values = {'COGNITO_DOMAIN': 'https://' + domain, 'COGNITO_CUSTOM_DOMAIN': domain}
lines = file.read_text().splitlines()
lines = [line for line in lines if line.split('=', 1)[0] not in values]
lines += [key + '=' + value for key, value in values.items()]
fd = os.open(file, os.O_WRONLY | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as output:
    output.write('\n'.join(lines) + '\n')
print('Custom Cognito domain configured. Restart the backend.')
