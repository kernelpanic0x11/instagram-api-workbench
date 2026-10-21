import pathlib,zipfile,struct,json,re,collections
ROOT=pathlib.Path(__file__).resolve().parent
if not list((ROOT/'apks').glob('*.apk')):raise SystemExit('No APK inputs found; nothing was overwritten. See docs/REPRODUCING.md.')
out=ROOT/'evidence';out.mkdir(exist_ok=True); inventory=[]; classes=[]; urls=[]; routes=[]; libraries=[]; counts=[]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def dexstrings(b):
 n,o=u32(b,56),u32(b,60); result=[]
 for i in range(n):
  p=u32(b,o+4*i)
  while b[p]&128:p+=1
  p+=1; end=b.index(0,p)
  result.append((p,b[p:end].decode('utf-8','replace')))
 return result
for apk in sorted((ROOT/'apks').glob('*.apk')):
 with zipfile.ZipFile(apk) as z:
  for f in z.infolist():
   inventory.append({'apk':apk.name,'member':f.filename,'size':f.file_size,'compressed_size':f.compress_size})
   if f.filename.endswith('.so'): libraries.append({'apk':apk.name,'member':f.filename,'bytes':f.file_size})
   if not re.fullmatch(r'classes\d*\.dex',f.filename): continue
   b=z.read(f); ss=dexstrings(b); types=[u32(b,u32(b,68)+4*i) for i in range(u32(b,64))]
   nc,co=u32(b,96),u32(b,100)
   for i in range(nc):
    idx=u32(b,co+32*i); name=ss[types[idx]][1]
    classes.append({'apk':apk.name,'dex':f.filename,'class':name,'class_def_offset':co+32*i})
   counts.append({'apk':apk.name,'dex':f.filename,'strings':len(ss),'defined_classes':nc,'method_ids':u32(b,88)})
   for off,s in ss:
    if re.search(r'https?://[^\s"<>]+',s): urls.append({'apk':apk.name,'dex':f.filename,'offset':off,'value':s})
    if re.fullmatch(r'(?:/?api/)?v[0-9]+/[^\s]{1,250}',s): routes.append({'apk':apk.name,'dex':f.filename,'offset':off,'value':s})
for name,data in [('archive-inventory',inventory),('native-libraries',libraries),('dex-counts',counts)]: (out/(name+'.json')).write_text(json.dumps(data,indent=2))
for name,data in [('classes',classes),('url-strings',urls),('route-strings',routes)]:
 with (out/(name+'.jsonl')).open('w') as f:
  for row in data:f.write(json.dumps(row)+'\n')
summary={'apk_count':len(list((ROOT/'apks').glob('*.apk'))),'archive_members':len(inventory),'dex_files':len(counts),'class_definitions':len(classes),'native_libraries':len(libraries),'url_string_records':len(urls),'route_string_records':len(routes),'dex_counts':counts}
(out/'inventory-summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
