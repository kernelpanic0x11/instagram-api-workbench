#!/usr/bin/env python3
"""Deploy Cognito, then write only non-secret resource IDs to the local service config."""
import argparse
import json
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--profile', default='admin')
p.add_argument('--region', default='us-east-1')
p.add_argument('--origin', default='http://127.0.0.1:8787')
p.add_argument('--stack', default='rea-auth')
p.add_argument('--model-id', default='')
args = p.parse_args()
if args.origin.endswith('/'):
    p.error('--origin must not end with a slash')
aws = ['aws', '--profile', args.profile, '--region', args.region, '--no-cli-pager']
subprocess.run(aws + ['sts', 'get-caller-identity', '--query', 'Account', '--output', 'text'], check=True)
subprocess.run(aws + ['cloudformation', 'deploy', '--stack-name', args.stack, '--template-file', str(root / 'infra/auth-stack.json'), '--parameter-overrides', 'AppOrigin=' + args.origin, '--no-fail-on-empty-changeset'], check=True)
result = subprocess.run(aws + ['cloudformation', 'describe-stacks', '--stack-name', args.stack, '--query', 'Stacks[0].Outputs', '--output', 'json'], check=True, capture_output=True, text=True)
outputs = {o['OutputKey']: o['OutputValue'] for o in json.loads(result.stdout)}
values = {
    'AWS_PROFILE': args.profile, 'AWS_REGION': args.region, 'PUBLIC_ORIGIN': args.origin,
    'COGNITO_DOMAIN': outputs['CognitoDomain'], 'COGNITO_USER_POOL_ID': outputs['CognitoUserPoolId'],
    'COGNITO_CLIENT_ID': outputs['CognitoClientId'],
}
if args.model_id:
    values['BEDROCK_MODEL_ID'] = args.model_id
file = root / 'be/.env'
lines = file.read_text().splitlines() if file.exists() else []
lines = [line for line in lines if line.split('=', 1)[0] not in values]
lines += [f'{key}={value}' for key, value in values.items()]
fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as output:
    output.write('\n'.join(lines) + '\n')
print('Cognito configured. Restart the backend, then use its sign-in button.')
