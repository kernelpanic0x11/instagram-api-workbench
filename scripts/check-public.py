"""Check the release tree without printing possible secret values."""
from pathlib import Path
import re,gzip,subprocess,json,sys
root=Path(__file__).resolve().parents[1]
patterns={
 'credential':re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer\s+(?:IGT:2:)?[A-Za-z0-9._+/=-]{24,}|sessionid=[^\s;"\']{20,}|csrftoken=[A-Za-z0-9]{20,})'),
 'local-path':re.compile(r'/Users/|/(?:private/)?var/folders/|/data/app/~~'),
}
failures=[];count=0
listing=subprocess.run(['git','-C',str(root),'ls-files','--cached','--others','--exclude-standard','-z'],capture_output=True)
paths=[root/name for name in listing.stdout.decode().split('\0') if name] if listing.returncode==0 else list(root.rglob('*'))
for p in paths:
 if not p.is_file() or any(x in {'.git','node_modules','__pycache__'} for x in p.relative_to(root).parts):continue
 if p.resolve()==Path(__file__).resolve():continue
 rel=p.relative_to(root).as_posix();count+=1
 if p.suffix in {'.apk','.jar','.bin','.har','.saz','.pcap','.pcapng','.stderr'} or p.name.startswith(('.env','.secrets')) or any(part in {'sessions','runs','.auth','browser-profile'} for part in p.relative_to(root).parts):
  failures.append((rel,'excluded artifact'));continue
 data=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
 text=data.decode('utf8','replace')
 if p.suffix=='.json':
  try:
   value=json.loads(text)
   if isinstance(value,dict) and ('authorization_data' in value or isinstance(value.get('cookies'),dict) and 'sessionid' in value['cookies']):
    failures.append((rel,'saved authentication state'))
  except ValueError:pass
 for name,pat in patterns.items():
  if pat.search(text):failures.append((rel,name))
# Inspect staged bytes separately: an edited worktree can hide an older secret
# that is still in the index. Deleted worktree files can also remain staged.
staged=subprocess.check_output(['git','-C',str(root),'diff','--cached','--name-only','--diff-filter=ACMR','-z']).decode().split('\0')
for rel in filter(None,staged):
 if rel=='scripts/check-public.py':continue
 path=Path(rel)
 if path.name.startswith(('.env','.secrets')) or any(part in {'sessions','runs','.auth','browser-profile'} for part in path.parts):
  failures.append((rel,'excluded staged artifact'));continue
 data=subprocess.check_output(['git','-C',str(root),'show',':'+rel])
 if path.suffix=='.gz':data=gzip.decompress(data)
 text=data.decode('utf8','replace')
 for name,pat in patterns.items():
  if pat.search(text):failures.append((rel,'staged '+name))
 if path.suffix=='.json':
  try:
   value=json.loads(text)
   if isinstance(value,dict) and ('authorization_data' in value or isinstance(value.get('cookies'),dict) and 'sessionid' in value['cookies']):
    failures.append((rel,'staged authentication state'))
  except ValueError:pass
if '--history' in sys.argv:
 # Scan every locally reachable blob, including outgoing commits. This also
 # catches a credential added and then removed before a later clean commit.
 objects=subprocess.check_output(['git','-C',str(root),'rev-list','--objects','--all']).decode().splitlines()
 for entry in objects:
  oid,_,rel=entry.partition(' ')
  if rel=='scripts/check-public.py':continue
  kind=subprocess.check_output(['git','-C',str(root),'cat-file','-t',oid]).strip()
  if kind!=b'blob':continue
  data=subprocess.check_output(['git','-C',str(root),'cat-file','blob',oid])
  if rel.endswith('.gz'):data=gzip.decompress(data)
  text=data.decode('utf8','replace')
  for name,pat in patterns.items():
   if pat.search(text):failures.append(('git blob '+oid,'history '+name))
if failures:
 for path,kind in failures:print(f'{kind}: {path}')
 raise SystemExit(1)
print(f'Public artifact scan passed: {count} files; no matched secret/local-path patterns. This is a bounded pattern check, not proof of absence.')
