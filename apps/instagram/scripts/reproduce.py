#!/usr/bin/env python3
"""Build a separate APK-to-OpenAPI analysis workspace; never overwrite the reference snapshot."""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
INSTAGRAM_ROOT=Path(__file__).resolve().parents[1]
REFERENCE_SHA='4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b'
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while block:=f.read(1024*1024):h.update(block)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apk-dir',type=Path,default=INSTAGRAM_ROOT/'apks');p.add_argument('--output',type=Path,required=True);p.add_argument('--routes-only',action='store_true');p.add_argument('--profile',type=Path,default=INSTAGRAM_ROOT/'api/bulk-trace/profiles/instagram-451.json');p.add_argument('--package',default='unidentified');p.add_argument('--version',default='unidentified');p.add_argument('--install',action='store_true',help='Run npm ci --ignore-scripts in the new workspace if dependencies are missing');a=p.parse_args()
 inputs=sorted(a.apk_dir.resolve().glob('*.apk'));base=next((f for f in inputs if f.name=='base.apk'),None)
 if base is None:p.error('No base.apk found. Use scripts/pull-apks.py or supply your own APKs; see docs/REPRODUCING.md.')
 if a.output.exists():p.error('Output must be a new directory. Nothing overwritten.')
 base_sha=digest(base);profile=None
 if not a.routes_only:
  loader=importlib.util.spec_from_file_location('mapping_validator',INSTAGRAM_ROOT/'api/bulk-trace/extract.py');module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
  try:profile=module.load_profile(a.profile)
  except (ValueError,KeyError,TypeError) as error:p.error(str(error))
  if base_sha!=profile.get('apk_sha256'):p.error('APK/profile digest mismatch. Start with --routes-only, or validate a new profile as documented in docs/PORTING.md. No output created.')
 if not shutil.which('node') or not shutil.which('npm'):p.error('Node and npm are required. Run scripts/doctor.py.')
 if not a.install and not (INSTAGRAM_ROOT/'api/node_modules/yaml').is_dir():p.error('Install build dependencies first: cd api && npm ci --ignore-scripts; or pass --install.')
 identities=[]
 for apk in inputs:
  with zipfile.ZipFile(apk) as archive:
   bad=archive.testzip()
   if bad:p.error('ZIP integrity failure in '+apk.name)
   if apk==base and not any(name=='classes.dex' for name in archive.namelist()):p.error('base.apk has no standard classes.dex; packed/non-DEX targets need a different workflow.')
  identities.append({'name':apk.name,'bytes':apk.stat().st_size,'sha256':digest(apk)})
 # A Git checkout uses tracked and non-ignored source files. Archives use the release manifest.
 listing=subprocess.run(['git','-C',str(INSTAGRAM_ROOT),'ls-files','--cached','--others','--exclude-standard','-z'],capture_output=True)
 names=listing.stdout.decode().split('\0') if listing.returncode==0 else [x['path']for x in json.loads((INSTAGRAM_ROOT/'PUBLIC_EXPORT.json').read_text())['files']]+['PUBLIC_EXPORT.json']
 out=a.output.resolve();out.mkdir(parents=True)
 for name in filter(None,names):
  rel=Path(name)
  if rel.is_absolute() or '..' in rel.parts or any(part in {'.git','apks','tools','runs','node_modules','__pycache__','sessions','hosted'}for part in rel.parts):continue
  source=INSTAGRAM_ROOT/rel
  if not source.is_file():continue
  destination=out/rel;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
 (out/'apks').mkdir();(out/'evidence').mkdir(exist_ok=True)
 for apk,identity in zip(inputs,identities):
  destination=out/'apks'/apk.name;shutil.copy2(apk,destination)
  if digest(destination)!=identity['sha256']:raise SystemExit('APK input changed while copying; discard this incomplete run and retry.')
 reference_traces=not a.routes_only and base_sha==REFERENCE_SHA
 if not reference_traces:
  for relative in ['evidence','visibility','reels-trace','api/evidence','api/schema-evidence']:
   shutil.rmtree(out/relative,ignore_errors=True)
  (out/'evidence').mkdir();(out/'api/schema-evidence').mkdir()
  (out/'api/schema-evidence/schemas.json').write_text(json.dumps({'components':{'schemas':{}}})+'\n')
  (out/'api/operations.json').write_text('[]\n')
  (out/'api/bulk-trace/request-fields.json').write_text(json.dumps({'source_apk_sha256':base_sha,'operations':[],'note':'No validated request-field mappings applied to this input.'})+'\n')
  (out/'api/bulk-trace/response-contracts.json').write_text(json.dumps({'source_apk_sha256':base_sha,'operations':[],'parsers':{},'note':'No validated response mappings applied to this input.'})+'\n')
  (out/'api/bulk-trace/shared-contracts.json').write_text(json.dumps({'source_apk_sha256':base_sha,'rules':None,'note':'No validated shared mappings applied to this input.'})+'\n')
  (out/'REPORT.txt').unlink(missing_ok=True)
  for relative in ['api/helper-scan','api/method-scan']:
   for file in (out/relative).glob('*.json*'):file.unlink()
 target={'package':profile.get('package',a.package)if profile else a.package,'version':profile.get('version',a.version)if profile else a.version,'sha256':base_sha,'identity_status':'known digest profile' if profile else 'user-supplied labels; manifest identity not decoded'}
 (out/'api/target.json').write_text(json.dumps(target,indent=2)+'\n')
 if profile:(out/'api/bulk-trace/profiles/run-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
 dependencies=out/'api/node_modules'
 if (INSTAGRAM_ROOT/'api/node_modules/yaml').is_dir():shutil.copytree(INSTAGRAM_ROOT/'api/node_modules',dependencies) if os.name=='nt' else dependencies.symlink_to(INSTAGRAM_ROOT/'api/node_modules',target_is_directory=True)
 def run(command):
  print('+ '+' '.join(command),flush=True)
  with (out/'run-log.txt').open('a')as log:
   log.write('+ '+' '.join(command)+'\n')
   process=subprocess.Popen(command,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   for line in process.stdout:print(line,end='',flush=True);log.write(line)
   if process.wait():raise SystemExit('Step failed; see run-log.txt. The reference checkout was not changed.')
 reference_inputs={name:digest(out/name)for name in ['api/operations.json','api/schema-evidence/schemas.json','api/make-operations.py']}if reference_traces else {}
 if not dependencies.exists():run(['npm','ci','--ignore-scripts','--prefix','api'])
 run([sys.executable,'inventory.py']);run([sys.executable,'index_strings.py']);run([sys.executable,'api/extraction/extract.py'])
 if a.routes_only:(out/'api/bulk-trace/operations.json').write_text(json.dumps({'operations':[],'stats':{},'note':'Route-only extraction. No version-specific method mappings applied.'})+'\n')
 else:run([sys.executable,'api/bulk-trace/extract.py','--apk','apks/base.apk','--profile','api/bulk-trace/profiles/run-profile.json'])
 if reference_traces:run([sys.executable,'api/make-operations.py'])
 if reference_traces:run([sys.executable,'api/bulk-trace/trace-request-fields.py','--apk','apks/base.apk'])
 if reference_traces:run([sys.executable,'api/bulk-trace/trace-response-contracts.py','--apk','apks/base.apk'])
 if reference_traces:run([sys.executable,'api/bulk-trace/trace-shared-contracts.py','--apk','apks/base.apk'])
 for endpoint in ('comment','post'):
  if reference_traces:run([sys.executable,'api/bulk-trace/trace-comment-keywords.py','--endpoint',endpoint])
  else:(out/('api/bulk-trace/'+endpoint+'-keywords-evidence.json')).unlink(missing_ok=True)
  (out/('api/'+endpoint+'-keywords-observation.json')).unlink(missing_ok=True)
 (out/'api/read-validation-results.json').unlink(missing_ok=True)
 (out/'api/mobile-retest-results.json').unlink(missing_ok=True)
 (out/'api/additional-read-results.json').unlink(missing_ok=True)
 (out/'api/online-read-results.json').unlink(missing_ok=True)
 (out/'api/second-read-repair-results.json').unlink(missing_ok=True)
 (out/'api/remaining-read-results.json').unlink(missing_ok=True)
 (out/'api/read-repair-results.json').unlink(missing_ok=True)
 for filename in ('transport-validation-results.json','notification-transport-observation.json','notification-sdk-transport-observation.json','notification-http-transport-comparison.json'):
  (out/'api'/filename).unlink(missing_ok=True)
 if reference_traces:run([sys.executable,'api/bulk-trace/trace-read-repairs.py']);run([sys.executable,'api/bulk-trace/trace-remaining-reads.py'])
 else:
  (out/'api/remaining-read-review.json').unlink(missing_ok=True)
  (out/'api/remaining-read-audit.json').unlink(missing_ok=True)
  (out/'api/bulk-trace/remaining-read-evidence.json').unlink(missing_ok=True)
  (out/'api/read-repair-contracts.json').unlink(missing_ok=True)
  (out/'api/bulk-trace/read-repair-evidence.json').unlink(missing_ok=True)
 # An offline reproduction must never inherit the reference session's live checks.
 (out/'api/runtime-checks.json').write_text(json.dumps({'checks':[],'note':'Offline reproduction; no runtime requests made.'})+'\n')
 (out/'api/runtime-error-checks.json').write_text(json.dumps({'checks':[],'note':'Offline reproduction; no runtime requests made.'})+'\n')
 run(['node','api/build.mjs']);run(['node','api/validate.mjs'])
 spec=json.loads((out/'api/openapi.json').read_text());manifest={'completed_at':datetime.now(timezone.utc).isoformat(),'target':target,'inputs':identities,'mode':'route-only'if a.routes_only else 'profile-traced','mapping_profile_sha256':digest(out/'api/bulk-trace/profiles/run-profile.json')if profile else None,'reference_manual_traces_included':reference_traces,'reference_inputs_sha256':reference_inputs,'paths':len(spec['paths']),'operations':spec['x-coverage']['documentedOperations'],'tooling_sha256':{name:digest(out/name)for name in ['inventory.py','index_strings.py','scripts/reproduce.py','api/extraction/extract.py','api/bulk-trace/extract.py','api/build.mjs','api/validate.mjs']},'decode_errors':json.loads((out/'api/bulk-trace/operations.json').read_text()).get('stats',{}).get('errors',0),'tool_versions':{'python':sys.version.split()[0],'node':subprocess.check_output(['node','--version'],text=True).strip()},'outputs':{name:digest(out/name)for name in ['api/openapi.json','api/openapi.yaml','api/extraction/catalog.json','api/bulk-trace/operations.json']},'limitations':['Static configuration is not server behavior. No account requests made.','Only standard root classes*.dex members are indexed; packed/native/JS code is outside this pipeline.','Manifest labels on unknown APKs are user-supplied, not independently decoded.']}
 (out/'run-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(out/'RUN_REPORT.md').write_text('# Offline extraction result\n\nMode: '+manifest['mode']+'\n\nBase SHA-256: '+base_sha+'\n\nPaths: '+str(manifest['paths'])+'; traced operations: '+str(manifest['operations'])+'.\n\nSee run-manifest.json for input hashes, tool versions, output hashes and limits.\n')
 print(json.dumps({'output':str(out),'paths':manifest['paths'],'operations':manifest['operations'],'reference_manual_traces_included':reference_traces}),flush=True)
if __name__=='__main__':main()
