import struct,zipfile,json,pathlib,lzma,re
P=pathlib.Path(__file__).resolve().parent
wanted=set(range(0x6204,0x620c))|{i&65535 for i in [2131971894,2131971895,2131971896,2131982375]}
hits=[];files=[]
with zipfile.ZipFile(P.parents[1]/'apks/base.apk') as z:
 for name in z.namelist():
  if not name.startswith('assets/strings/') or not name.endswith('.frsc'):continue
  d=z.read(name)
  if d[:4]!=b'FRSC':continue
  n,offsettab=struct.unpack_from('<II',d,4);ranges=[struct.unpack_from('<HHH',d,12+6*i) for i in range(n)]
  files.append({'asset':name,'ranges':n,'offset_table':offsettab})
  for rid in wanted:
   for start,count,index in ranges:
    if start<=rid<start+count:
     ix=index+rid-start;off=struct.unpack_from('<I',d,offsettab+4*ix)[0];length=struct.unpack_from('<H',d,off)[0]
     hits.append({'asset':name,'resource_id':hex(0x7f130000|rid),'range_start':start,'range_count':count,'string_index':ix,'offset':off,'length':length,'value':d[off+2:off+2+length].decode('utf8','replace')})
 d=z.read('assets/strings/default.frsc.spo');streams=[]
 for m in re.finditer(bytes.fromhex('fd377a585a00'),d):
  de=lzma.LZMADecompressor();out=de.decompress(d[m.start():]);streams.append({'offset':m.start(),'decoded_bytes':len(out),'complete_xz_stream':de.eof,'header_hex':out[:16].hex()})
result={'scope':'Sparse FRSC locale asset range tables interpreted as little-endian uint16 start/count/base index and uint32 string offsets; target resource IDs only. Base default.frsc.spo not fully decoded: its XZ streams decode but use custom ST dictionary/token representation. No default English target text recovered.','files':files,'hits':hits,'default_xz_streams':streams}
(P/'frsc-resource-results.json').write_text(json.dumps(result,indent=2));print('files',len(files),'hits',len(hits));print(json.dumps(hits,indent=2))
