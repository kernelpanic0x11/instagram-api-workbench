import zipfile,struct,json,re,pathlib,collections
P=pathlib.Path(__file__).resolve().parent
pat=re.compile(r'long_reel|DISTRIBUTION_LIMIT|restricted_distribution|MBS_INSIGHTS_RECOMMENDATION_ELIGIBILITY',re.I)
W={i:1 for i in [0,1,4,7,10,11,12,13,14,15,16,17,18,29,30,33,39,40]}
for i in [2,5,8,19,21,22,25,26,28,31,32,34,35,41]:W[i]=2
for i in [3,6,9,20,23,27,36,37,38,42,43,44]:W[i]=3
W[24]=5
for a,b,w in [(0x2d,0x3d,2),(0x44,0x6d,2),(0x6e,0x72,3),(0x74,0x78,3),(0x7b,0x8f,1),(0x90,0xaf,2),(0xb0,0xcf,1),(0xd0,0xe2,2),(0xfa,0xfb,4),(0xfc,0xfd,3),(0xfe,0xff,2)]:
 for i in range(a,b+1):W[i]=w
stats=collections.Counter();hits=[];errors=[];calls=[];nearby=[]
with zipfile.ZipFile(P.parents[1]/'apks/base.apk') as z:
 for name in z.namelist():
  if not re.fullmatch(r'classes\d*\.dex',name):continue
  data=z.read(name);stats['dex_files']+=1
  def u32(o):return struct.unpack_from('<I',data,o)[0]
  def u16(o):return struct.unpack_from('<H',data,o)[0]
  def leb(o):
   n=0;s=0
   while True:
    b=data[o];o+=1;n|=(b&127)<<s;s+=7
    if b<128:return n,o
  sn,so=struct.unpack_from('<II',data,56);strings=[]
  for i in range(sn):
   o=leb(u32(so+i*4))[1];strings.append(data[o:data.index(0,o)].decode('utf8','replace'))
  wanted={i:s for i,s in enumerate(strings) if pat.search(s)}
  stats['matching_strings']+=len(wanted)
  tn,to=struct.unpack_from('<II',data,64);types=[strings[u32(to+i*4)] for i in range(tn)]
  pn,po=struct.unpack_from('<II',data,72)
  def proto(i):
   o=po+i*12;args=u32(o+8)
   return '('+(''.join(types[u16(args+4+k*2)] for k in range(u32(args))) if args else '')+')'+types[u32(o+4)]
  mn,mo=struct.unpack_from('<II',data,88)
  def meth(i):
   c,p,n=struct.unpack_from('<HHI',data,mo+8*i);return types[c]+'->'+strings[n]+proto(p)
  targets={i:meth(i) for i in range(mn) if meth(i).startswith(('LX/0L1j;->A00(', 'LX/01pP;->', 'LX/0Y3h;->'))}
  cn,co=struct.unpack_from('<II',data,96)
  for c in range(cn):
   o=u32(co+c*32+24)
   if not o:continue
   sizes=[]
   for _ in range(4):n,o=leb(o);sizes.append(n)
   for _ in range(sizes[0]+sizes[1]):_,o=leb(o);_,o=leb(o)
   for group in sizes[2:]:
    mid=0
    for _ in range(group):
     diff,o=leb(o);mid+=diff;access,o=leb(o);code,o=leb(o)
     if not code:continue
     stats['methods_with_code']+=1
     size=u32(code+12);ins=code+16;pc=0;found=[];foundcalls=[];near=[]
     nearby_method=True
     try:
      while pc<size:
       op=u16(ins+pc*2);lo=op&255
       if lo==0 and op:
        if op==0x100:w=4+u16(ins+(pc+1)*2)*2
        elif op==0x200:w=2+u16(ins+(pc+1)*2)*4
        elif op==0x300:w=4+(u16(ins+(pc+1)*2)*u32(ins+(pc+2)*2)+1)//2
        else:raise ValueError('unknown payload '+hex(op))
       else:
        if lo not in W:raise ValueError('reserved opcode '+hex(lo))
        w=W[lo]
        if lo in range(0x6e,0x73) or lo in range(0x74,0x79):
         target=u16(ins+(pc+1)*2)
         if True:foundcalls.append({'dex':name,'caller':meth(mid),'callee':meth(target),'code_unit_offset':pc,'dex_byte_offset':ins+pc*2})
        if lo in [0x1a,0x1b]:
         sid=u16(ins+(pc+1)*2) if lo==0x1a else u32(ins+(pc+1)*2)
         if nearby_method:near.append({'dex':name,'method':meth(mid),'code_unit_offset':pc,'value':strings[sid]})
         if sid in wanted:found.append({'dex':name,'method_index':mid,'method':meth(mid),'code_unit_offset':pc,'dex_byte_offset':ins+pc*2,'string_index':sid,'value':wanted[sid]})
       pc+=w
      if pc!=size:raise ValueError('instruction overrun')
      stats['decoded_methods']+=1
      if found:hits+=found;calls+=foundcalls;nearby+=near
     except Exception as e:
      stats['decode_errors']+=1;errors.append({'dex':name,'method':meth(mid),'error':str(e)})
  print(name,len(hits),flush=True)
(P/'dex-string-references.json').write_text(json.dumps({'scope':'base.apk root classes*.dex; correctly decoded instruction boundaries; const-string and const-string/jumbo only','stats':dict(stats),'hits':hits,'calls':calls,'nearby_method_strings':nearby,'errors':errors},indent=2))
print(dict(stats))
