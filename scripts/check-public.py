"""Check the release tree without printing possible secret values."""
from pathlib import Path
import re,gzip,subprocess
root=Path(__file__).resolve().parents[1]
patterns={
 'credential':re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{24,}|sessionid=[^\s;"\']{20,}|csrftoken=[A-Za-z0-9]{20,})'),
 'local-path':re.compile(r'/Users/|/(?:private/)?var/folders/|/data/app/~~'),
}
failures=[];count=0
listing=subprocess.run(['git','-C',str(root),'ls-files','--cached','--others','--exclude-standard','-z'],capture_output=True)
paths=[root/name for name in listing.stdout.decode().split('\0') if name] if listing.returncode==0 else list(root.rglob('*'))
for p in paths:
 if not p.is_file() or any(x in {'.git','node_modules','__pycache__'} for x in p.relative_to(root).parts):continue
 if p.resolve()==Path(__file__).resolve():continue
 rel=p.relative_to(root).as_posix();count+=1
 if p.suffix in {'.apk','.jar','.bin','.har','.saz','.pcap','.pcapng','.stderr'} or p.name.startswith('.env'):
  failures.append((rel,'excluded artifact'));continue
 data=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
 text=data.decode('utf8','replace')
 for name,pat in patterns.items():
  if pat.search(text):failures.append((rel,name))
if failures:
 for path,kind in failures:print(f'{kind}: {path}')
 raise SystemExit(1)
print(f'Public artifact scan passed: {count} files; no matched secret/local-path patterns. This is a bounded pattern check, not proof of absence.')
