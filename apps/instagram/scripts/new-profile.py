#!/usr/bin/env python3
"""Create a deliberately unusable draft mapping profile for a new APK."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apk',type=Path,required=True);p.add_argument('--package',required=True);p.add_argument('--version',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if not a.apk.is_file():p.error('APK not found')
if a.output.exists():p.error('Output exists; nothing overwritten')
h=hashlib.sha256()
with a.apk.open('rb')as f:
 while block:=f.read(1024*1024):h.update(block)
profile={'name':a.package+' '+a.version,'package':a.package,'version':a.version,'apk_sha256':h.hexdigest(),'status':'draft','provenance':'TODO: record APK-bound method/enum/field evidence before marking validated. See docs/PORTING.md.','helpers':[],'method_helpers':[],'path_helpers':[],'enum':[],'set_method':None,'route_field':None,'method_field':None}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(profile,indent=2)+'\n');print('Draft profile created. It is intentionally rejected by the scanner until validated: '+str(a.output))
