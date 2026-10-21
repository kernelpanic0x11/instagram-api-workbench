#!/usr/bin/env python3
"""Read installed APKs from a user-authorized Android device. Does not read app data."""
import argparse,hashlib,json,re,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',default='com.instagram.android');p.add_argument('--serial');p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'apks');p.add_argument('--adb',default='adb');a=p.parse_args()
 if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+',a.package):p.error('Invalid package name')
 adb=shutil.which(a.adb)
 if not adb:p.error('adb not found. Install Android SDK Platform Tools; see docs/REPRODUCING.md.')
 command=[adb]+(['-s',a.serial] if a.serial else [])
 def run(*args):
  r=subprocess.run([*command,*args],capture_output=True,text=True)
  if r.returncode:p.error('ADB command failed; check device authorization and serial. '+r.stderr.strip())
  return r.stdout
 devices=[line.split('\t') for line in run('devices').splitlines()[1:] if '\t' in line]
 if not a.serial and len([d for d in devices if d[1]=='device'])!=1:p.error('Connect exactly one authorized device, or supply --serial. Accept the USB-debugging prompt on your phone yourself.')
 paths=[line.removeprefix('package:').strip() for line in run('shell','pm','path',a.package).splitlines() if line.startswith('package:')]
 if not paths:p.error('Package not found on the selected device')
 if any(not re.fullmatch(r'/[A-Za-z0-9_./~+=-]+\.apk',path) for path in paths):p.error('Unexpected APK path format')
 names=[Path(path).name for path in paths]
 if len(set(names))!=len(names) or 'base.apk' not in names:p.error('Expected unique split APK names and base.apk')
 a.output.mkdir(parents=True,exist_ok=True)
 if any((a.output/name).exists() for name in names):p.error('Output already contains APKs; choose an empty output directory. Nothing overwritten.')
 records=[]
 for remote,name in zip(paths,names):
  destination=a.output/name;run('pull',remote,str(destination))
  with zipfile.ZipFile(destination) as archive:
   if archive.testzip() is not None:raise SystemExit('APK ZIP integrity failed: '+name)
  digest=hashlib.sha256(destination.read_bytes()).hexdigest()
  remote_result=subprocess.run([*command,'shell','sha256sum',remote],capture_output=True,text=True)
  match=re.match(r'^([a-fA-F0-9]{64})\s',remote_result.stdout)
  verified=remote_result.returncode==0 and bool(match)
  if verified and match[1].lower()!=digest:raise SystemExit('Transfer digest mismatch: '+name)
  records.append({'name':name,'bytes':destination.stat().st_size,'sha256':digest,'remote_sha256_verified':bool(verified)})
  print('Acquired '+name,flush=True)
 manifest={'package':a.package,'acquired_at':datetime.now(timezone.utc).isoformat(),'files':records,'note':'No device serial, installation paths, account data, cookies or tokens are recorded.'}
 (a.output/'acquisition.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'apks':len(records),'output':str(a.output),'all_transfer_hashes_verified':all(r['remote_sha256_verified'] for r in records)}))
if __name__=='__main__':main()
