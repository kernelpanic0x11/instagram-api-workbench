"""Clean-export and synthetic-input regression checks. No device or credentials required."""
import hashlib,json,os,shutil,struct,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ReproductionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.directory=tempfile.TemporaryDirectory(prefix='instagram-repro-tests-');cls.copy=Path(cls.directory.name)/'checkout'
  shutil.copytree(ROOT,cls.copy,ignore=shutil.ignore_patterns('.git','node_modules','apks','runs','tools','__pycache__','hosted'))
  if (ROOT/'api/node_modules').is_dir():(cls.copy/'api/node_modules').symlink_to(ROOT/'api/node_modules',target_is_directory=True)
 @classmethod
 def tearDownClass(cls):cls.directory.cleanup()
 def run_script(self,*args):return subprocess.run([sys.executable,*args],cwd=self.copy,capture_output=True,text=True)
 def test_public_reports_regenerate_without_raw_private_metadata(self):
  for script in ['reels-trace/build_report.py','visibility/build_trace.py','build_report.py']:
   r=self.run_script(script);self.assertEqual(r.returncode,0,r.stderr)
  index=json.loads((self.copy/'reels-trace/evidence-index.json').read_text());self.assertTrue(index['configure-request']['metadata_omitted']);self.assertIsNone(index['configure-request']['operation'])
 def test_helper_rank_reads_compressed_export(self):
  (self.copy/'api/helper-scan/route-method-calls.json').unlink(missing_ok=True)
  r=self.run_script('api/helper-scan/rank.py');self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(json.loads((self.copy/'api/helper-scan/ranked-helpers.json').read_text())['priority_for_verification'])
 def test_no_input_cannot_erase_reference_inventory(self):
  target=self.copy/'evidence/inventory-summary.json';before=target.read_bytes()
  for script in ['inventory.py','index_strings.py']:
   r=self.run_script(script);self.assertNotEqual(r.returncode,0);self.assertIn('No APK inputs',r.stderr)
  self.assertEqual(target.read_bytes(),before)
 def test_mismatched_apk_rejected_before_output(self):
  apk=Path(self.directory.name)/'foreign.apk';apk.write_bytes(b'not the reference APK');output=Path(self.directory.name)/'should-not-exist.json'
  r=self.run_script('api/bulk-trace/extract.py','--apk',str(apk),'--output',str(output));self.assertNotEqual(r.returncode,0);self.assertIn('does not match',r.stderr);self.assertFalse(output.exists())
 def test_draft_profile_is_rejected_before_creating_workspace(self):
  inputs=Path(self.directory.name)/'draft-input';inputs.mkdir();(inputs/'base.apk').write_bytes(b'fixture')
  profile=Path(self.directory.name)/'draft.json'
  r=self.run_script('scripts/new-profile.py','--apk',str(inputs/'base.apk'),'--package','example.fixture','--version','fixture','--output',str(profile));self.assertEqual(r.returncode,0,r.stderr)
  output=Path(self.directory.name)/'draft-output';r=self.run_script('scripts/reproduce.py','--apk-dir',str(inputs),'--profile',str(profile),'--output',str(output));self.assertNotEqual(r.returncode,0);self.assertIn('draft',r.stderr);self.assertFalse(output.exists())
 def test_raw_envelope_metadata_remains_available(self):
  p=self.copy/'reels-trace/configure-request.json';value=json.loads(p.read_text());record=value.get('structuredContent',value);record['operation']='fixture-operation';record['parameters']={'fixture':True};p.write_text(json.dumps({'structuredContent':record}))
  r=self.run_script('reels-trace/build_report.py');self.assertEqual(r.returncode,0,r.stderr)
  item=json.loads((self.copy/'reels-trace/evidence-index.json').read_text())['configure-request'];self.assertEqual(item['operation'],'fixture-operation');self.assertEqual(item['parameters'],{'fixture':True});self.assertEqual(item['metadata_omitted'],[])
 def test_missing_jadx_capture_helper_exits_instead_of_hanging(self):
  if not shutil.which('node') or not shutil.which('sh'):self.skipTest('POSIX Node capture helper')
  env={k:v for k,v in os.environ.items()if k!='REA_JADX_MCP_JAR'}
  r=subprocess.run(['node','visibility/rea-session.mjs','--output-dir',str(Path(self.directory.name)/'missing-jadx')],cwd=self.copy,env=env,capture_output=True,text=True,timeout=5);self.assertNotEqual(r.returncode,0);self.assertIn('REA_JADX_MCP_JAR',r.stderr)
 def test_jadx_setup_does_not_overwrite_a_mismatching_engine(self):
  output=Path(self.directory.name)/'fake-engine.jar';output.write_bytes(b'fixture')
  r=self.run_script('scripts/setup-jadx.py','--output',str(output));self.assertNotEqual(r.returncode,0);self.assertIn('not overwritten',r.stderr);self.assertEqual(output.read_bytes(),b'fixture')
 def test_apk_acquisition_records_hashes_without_device_or_install_paths(self):
  if os.name=='nt':self.skipTest('Synthetic executable adb fixture uses a POSIX shebang')
  fixture=Path(self.directory.name)/'acquire-fixture.apk'
  with zipfile.ZipFile(fixture,'w')as z:z.writestr('fixture.txt','fixture')
  adb=Path(self.directory.name)/'fixture-adb';adb.write_text('#!'+sys.executable+'\n'+"import hashlib,os,shutil,sys\nfrom pathlib import Path\na=sys.argv[1:];src=Path(os.environ['TEST_APK_FIXTURE'])\nif a==['devices']:print('List of devices attached\\nfixture-device\\tdevice')\nelif a[:3]==['shell','pm','path']:print('package:/fixture/install/base.apk\\npackage:/fixture/install/split_config.apk')\nelif a[0]=='pull':shutil.copyfile(src,a[2])\nelif a[:2]==['shell','sha256sum']:print(hashlib.sha256(src.read_bytes()).hexdigest()+'  '+a[2])\nelse:sys.exit(2)\n");adb.chmod(0o700)
  output=Path(self.directory.name)/'acquired'
  r=subprocess.run([sys.executable,'scripts/pull-apks.py','--adb',str(adb),'--output',str(output),'--package','example.fixture'],cwd=self.copy,env={**os.environ,'TEST_APK_FIXTURE':str(fixture)},capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr);body=(output/'acquisition.json').read_text();manifest=json.loads(body);self.assertEqual(len(manifest['files']),2);self.assertTrue(all(f['remote_sha256_verified']for f in manifest['files']));self.assertNotIn('fixture-device',body);self.assertNotIn('/fixture/install',body)
 def test_route_only_pipeline_is_isolated_and_does_not_invent_methods(self):
  if not (ROOT/'api/node_modules/yaml').exists():self.skipTest('Install api build dependencies to run the integrated pipeline check')
  # Minimal parser fixture: one DEX string, no methods/classes; not an installable APK.
  inputs=Path(self.directory.name)/'inputs';inputs.mkdir();route=b'users/example/';dex=bytearray(116+1+len(route)+1);dex[:8]=b'dex\n035\0';struct.pack_into('<II',dex,56,1,112);struct.pack_into('<I',dex,112,116);dex[116:]=bytes([len(route)])+route+b'\0'
  with zipfile.ZipFile(inputs/'base.apk','w')as z:z.writestr('classes.dex',dex)
  output=Path(self.directory.name)/'route-only'
  r=self.run_script('scripts/reproduce.py','--apk-dir',str(inputs),'--output',str(output),'--routes-only','--package','example.fixture','--version','fixture');self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  manifest=json.loads((output/'run-manifest.json').read_text());spec=json.loads((output/'api/openapi.json').read_text())
  self.assertEqual(manifest['operations'],0);self.assertEqual(manifest['paths'],1);self.assertFalse(manifest['reference_manual_traces_included']);self.assertEqual(spec['x-source']['sha256'],hashlib.sha256((inputs/'base.apk').read_bytes()).hexdigest());self.assertEqual(spec['info']['version'],'fixture');self.assertEqual(spec['components']['schemas'],{});self.assertFalse((output/'visibility').exists())
  hosted=Path(self.directory.name)/'hosted-fixture';r=subprocess.run(['node','api/build-hosted.mjs',str(hosted)],cwd=output,capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('0 traced operations',(hosted/'hosted.mjs').read_text());self.assertNotIn('679 traced operations',(hosted/'hosted.mjs').read_text());r=subprocess.run(['node','--check',str(hosted/'hosted.mjs')],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  again=self.run_script('scripts/reproduce.py','--apk-dir',str(inputs),'--output',str(output),'--routes-only');self.assertNotEqual(again.returncode,0);self.assertIn('Nothing overwritten',again.stderr)
if __name__=='__main__':unittest.main()
