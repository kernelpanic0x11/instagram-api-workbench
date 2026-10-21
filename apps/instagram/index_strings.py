import pathlib,struct,zipfile,gzip,json,re,collections,io
p=pathlib.Path(__file__).resolve().parent;counts=collections.Counter()
pattern=re.compile(r'^(?:/?api/v\d+/)?(?:accounts|feed|clips|direct_v2|media|users|friendships|discover|stories|ads|graphql|logging|qe|launcher|upload|rupload|consent|privacy|notifications|push|challenge|bloks)/[^\s]{0,300}$')
if not list((p/'apks').glob('*.apk')):raise SystemExit('No APK inputs found; nothing was overwritten. See docs/REPRODUCING.md.')
(p/'evidence').mkdir(exist_ok=True)
with (p/'evidence/all-dex-strings.jsonl.gz').open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as zipped,io.TextIOWrapper(zipped,encoding='utf8') as allout,(p/'evidence/feature-route-candidates.jsonl').open('w') as routes:
 for apk in sorted((p/'apks').glob('*.apk')):
  with zipfile.ZipFile(apk) as z:
   for n in z.namelist():
    if not re.fullmatch(r'classes\d*\.dex',n):continue
    b=z.read(n);num,off=struct.unpack_from('<II',b,56)
    for idx in range(num):
     at=struct.unpack_from('<I',b,off+4*idx)[0]
     while b[at]&128:at+=1
     at+=1;s=b[at:b.index(0,at)].decode('utf-8','replace');r={'apk':apk.name,'dex':n,'string_index':idx,'offset':at,'value':s};line=json.dumps(r)+'\n';allout.write(line);counts['strings']+=1
     if pattern.fullmatch(s):routes.write(line);counts['route_candidates']+=1
print(dict(counts))
