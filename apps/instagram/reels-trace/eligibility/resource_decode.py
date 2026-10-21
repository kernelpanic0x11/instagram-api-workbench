import struct,zipfile,json,pathlib,collections
P=pathlib.Path(__file__).resolve().parent
wanted=set(range(0x7f136204,0x7f13620c))|{2131971894,2131971895,2131971896,2131982375}
stats=collections.Counter();hits=[];errors=[]
def pool(d,o):
 t,hs,sz=struct.unpack_from('<HHI',d,o);n,styles,flags,start,sty=struct.unpack_from('<IIIII',d,o+8)
 def ln(p,wide=False):
  if wide:
   a=struct.unpack_from('<H',d,p)[0];p+=2
   if a&0x8000:return ((a&0x7fff)<<16)|struct.unpack_from('<H',d,p)[0],p+2
   return a,p
  a=d[p];p+=1
  if a&128:return ((a&127)<<8)|d[p],p+1
  return a,p
 out=[]
 for i in range(n):
  p=o+start+struct.unpack_from('<I',d,o+hs+4*i)[0]
  if flags&256:
   _,p=ln(p);l,p=ln(p);out.append(d[p:p+l].decode('utf8','replace'))
  else:
   l,p=ln(p,True);out.append(d[p:p+2*l].decode('utf-16le','replace'))
 return out
for apk in sorted((P.parents[1]/'apks').glob('*.apk')):
 with zipfile.ZipFile(apk) as z:
  if 'resources.arsc' not in z.namelist():continue
  d=z.read('resources.arsc');stats['arsc_files']+=1
  _,hs,size=struct.unpack_from('<HHI',d,0);o=hs;globalstrings=[]
  while o<size:
   typ,ch,sz=struct.unpack_from('<HHI',d,o)
   if not sz:raise ValueError('zero chunk')
   if typ==1:globalstrings=pool(d,o)
   if typ==0x200:
    pid=struct.unpack_from('<I',d,o+8)[0];typeoff=struct.unpack_from('<I',d,o+268)[0];keyoff=struct.unpack_from('<I',d,o+276)[0]
    types=pool(d,o+typeoff);keys=pool(d,o+keyoff);typeid_offset=struct.unpack_from('<I',d,o+284)[0] if ch>=288 else 0
    p=o+ch
    while p<o+sz:
     tt,th,ts=struct.unpack_from('<HHI',d,p)
     if tt==0x201:
      stats['type_chunks']+=1;tid,flags=struct.unpack_from('<BB',d,p+8);cnt,start=struct.unpack_from('<II',d,p+12);cfgsz=struct.unpack_from('<I',d,p+20)[0];cfg=d[p+20:p+20+cfgsz]
      offsets=[]
      if flags&1:
       stats['sparse_chunks']+=1
       for j in range(cnt):
        idx,off=struct.unpack_from('<HH',d,p+th+j*4);offsets.append((idx,off*4))
      elif flags&2:
       stats['offset16_chunks']+=1
       for j in range(cnt):
        off=struct.unpack_from('<H',d,p+th+j*2)[0]
        if off!=0xffff:offsets.append((j,off*4))
      else:
       for j in range(cnt):
        off=struct.unpack_from('<I',d,p+th+j*4)[0]
        if off!=0xffffffff:offsets.append((j,off))
      stats['entries']+=len(offsets)
      for idx,off in offsets:
       rid=(pid<<24)|((tid+typeid_offset)<<16)|idx
       if rid not in wanted:continue
       e=p+start+off;es,ef,key=struct.unpack_from('<HHI',d,e)
       rec={'apk':apk.name,'resource_id':hex(rid),'resource_id_decimal':rid,'type':types[tid-1],'key':keys[key] if key<len(keys) else key,'arsc_entry_offset':e,'config_hex':cfg.hex(),'entry_flags':ef}
       if ef&1:rec['value']='COMPLEX_ENTRY_NOT_DECODED'
       elif ef&8:
        dt=ef>>8;v=key;rec.update(data_type=dt,raw_value=v,compact=True);rec['value']=globalstrings[v] if dt==3 else v
       else:
        vs,res,dt,v=struct.unpack_from('<HBBI',d,e+es);rec.update(data_type=dt,raw_value=v);rec['value']=globalstrings[v] if dt==3 else v
       hits.append(rec)
     p+=ts
   o+=sz
(P/'resource-strings.json').write_text(json.dumps({'scope':'All local APK resources.arsc tables; target IDs only. String pools UTF8/UTF16; sparse, offset16 and standard type entry offsets supported; simple values supported, complex entries marked. Config bytes retained verbatim.','stats':dict(stats),'wanted':[hex(i) for i in sorted(wanted)],'hits':hits,'errors':errors},indent=2))
print(dict(stats))
for h in hits:print(h['resource_id'],h['key'],repr(h['value']),h['config_hex'])
