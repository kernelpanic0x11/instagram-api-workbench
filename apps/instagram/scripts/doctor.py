#!/usr/bin/env python3
"""Check prerequisites without installing software or connecting to a phone."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
JADX_SHA='6e5eacf500b64292bfb73c49797c1958f6ee44646e43e868039ae7feb573ff75'
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--android',action='store_true',help='Also require adb, a full JDK 17+, and the pinned JADX engine');a=parser.parse_args()
 checks=[{'name':'Python 3.10+','ok':sys.version_info>=(3,10)}]
 for name,args,minimum in [('node',['--version'],20),('npm',['--version'],None)]+([('adb',['version'],None),('java',['-version'],17),('javac',['-version'],17)] if a.android else []):
  executable=shutil.which(name);version='';success=False
  if executable:
   r=subprocess.run([executable,*args],capture_output=True,text=True);success=r.returncode==0;version=(r.stdout+r.stderr).splitlines()[0] if r.stdout+r.stderr else ''
  match=re.search(r'(?:version\s+"?|javac\s+|^v?)(\d+)(?:\.(\d+))?',version)
  ok=bool(executable) and success and (minimum is None or bool(match) and int(match[1])>=minimum)
  if name=='node' and match and int(match[1])==20:ok=ok and int(match[2] or 0)>=11
  checks.append({'name':name,'ok':ok,'version':version,'help':None if ok else 'See docs/REPRODUCING.md'})
 if a.android:
  jar=Path(os.environ.get('REA_JADX_MCP_JAR',''))
  checks.append({'name':'JADX headless MCP 0.7.1 SHA-256','ok':jar.is_file() and hashlib.sha256(jar.read_bytes()).hexdigest()==JADX_SHA,'help':'Run scripts/setup-jadx.py and export REA_JADX_MCP_JAR; see docs/REPRODUCING.md'})
 print(json.dumps({'ready':all(c['ok'] for c in checks),'checks':checks},indent=2));return 0 if all(c['ok'] for c in checks) else 1
if __name__=='__main__':raise SystemExit(main())
