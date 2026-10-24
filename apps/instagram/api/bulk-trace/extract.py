#!/usr/bin/env python3
"""Conservative basic-block DEX request configuration trace, no network access."""
import argparse,collections,hashlib,json,re,struct,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
W={i:1 for i in [0,1,4,7,10,11,12,13,14,15,16,17,18,29,30,33,39,40]}
for i in [2,5,8,19,21,22,25,26,28,31,32,34,35,41]:W[i]=2
for i in [3,6,9,20,23,27,36,37,38,42,43,44]:W[i]=3
W[24]=5
for a,b,w in [(0x2d,0x3d,2),(0x44,0x6d,2),(0x6e,0x72,3),(0x74,0x78,3),(0x7b,0x8f,1),(0x90,0xaf,2),(0xb0,0xcf,1),(0xd0,0xe2,2),(0xfa,0xfb,4),(0xfc,0xfd,3),(0xfe,0xff,2)]:
 for i in range(a,b+1):W[i]=w
class Dex:
 def __init__(self,data,name):
  self.d=data;self.name=name;self.strings=[]
  sn,so=struct.unpack_from('<II',data,56)
  for i in range(sn):
   o=self.leb(self.u32(so+i*4))[1];self.strings.append(data[o:data.index(0,o)].decode('utf8','replace'))
  tn,to=struct.unpack_from('<II',data,64);self.types=[self.strings[self.u32(to+i*4)] for i in range(tn)]
  pn,po=struct.unpack_from('<II',data,72);protos=[]
  for i in range(pn):
   o=po+i*12;args=self.u32(o+8)
   protos.append('('+(''.join(self.types[self.u16(args+4+k*2)] for k in range(self.u32(args))) if args else '')+')'+self.types[self.u32(o+4)])
  mn,mo=struct.unpack_from('<II',data,88);self.methods=[]
  for i in range(mn):
   c,p,n=struct.unpack_from('<HHI',data,mo+i*8);self.methods.append((self.types[c],self.strings[n],protos[p]))
  fn,fo=struct.unpack_from('<II',data,80);self.fields=[]
  for i in range(fn):
   c,t,n=struct.unpack_from('<HHI',data,fo+i*8);self.fields.append((self.types[c],self.strings[n],self.types[t]))
 def u16(self,o):return struct.unpack_from('<H',self.d,o)[0]
 def u32(self,o):return struct.unpack_from('<I',self.d,o)[0]
 def i32(self,o):return struct.unpack_from('<i',self.d,o)[0]
 def leb(self,o):
  n=s=0
  while True:
   b=self.d[o];o+=1;n|=(b&127)<<s;s+=7
   if b<128:return n,o
 def codes(self):
  cn,co=struct.unpack_from('<II',self.d,96)
  for c in range(cn):
   o=self.u32(co+c*32+24)
   if not o:continue
   sizes=[]
   for _ in range(4):n,o=self.leb(o);sizes.append(n)
   for _ in range(sizes[0]+sizes[1]):_,o=self.leb(o);_,o=self.leb(o)
   for group in sizes[2:]:
    mid=0
    for _ in range(group):
     diff,o=self.leb(o);mid+=diff;_,o=self.leb(o);code,o=self.leb(o)
     if code:yield mid,code
 def insns(self,code):
  size=self.u32(code+12);ins=code+16;pc=0;out=[];bounds={0}
  while pc<size:
   o=ins+pc*2;op=self.u16(o);lo=op&255
   if lo==0 and op:
    if op==0x100:w=4+self.u16(o+2)*2
    elif op==0x200:w=2+self.u16(o+2)*4
    elif op==0x300:w=4+(self.u16(o+2)*self.u32(o+4)+1)//2
    else:raise ValueError('payload')
    bounds.add(pc);bounds.add(pc+w)
   else:
    w=W[lo]
    if lo in [0x28,0x29,0x2a]:
     off=struct.unpack_from('<b',self.d,o+1)[0] if lo==0x28 else struct.unpack_from('<h' if lo==0x29 else '<i',self.d,o+2)[0]
     bounds.update([pc+off,pc+w])
    elif lo in range(0x32,0x3e):bounds.update([pc+struct.unpack_from('<h',self.d,o+2)[0],pc+w])
    elif lo in [0x2b,0x2c]:
     t=o+self.i32(o+2)*2;n=self.u16(t+2);start=t+8 if lo==0x2b else t+4+n*4
     bounds.add(pc+w)
     for k in range(n):bounds.add(pc+self.i32(start+k*4))
    elif lo in [0x0d,0x0e,0x0f,0x10,0x11,0x27]:bounds.update([pc,pc+w])
   out.append((pc,op,lo,w,o));pc+=w
  if pc!=size:raise ValueError('overrun')
  return out,bounds

def sig(t):return t[0]+'->'+t[1]+t[2]
DEFAULT_PROFILE=P/'profiles/instagram-451.json'
def load_profile(path):
 profile=json.loads(Path(path).read_text())
 if profile.get('status')!='validated':raise ValueError('Mapping profile is a draft. Trace and validate its selectors first; see docs/PORTING.md.')
 if not all(isinstance(profile.get(key),str) and profile[key] for key in ['name','package','version']):raise ValueError('Profile requires name, package and version labels')
 if not re.fullmatch(r'[a-f0-9]{64}',profile.get('apk_sha256','')):raise ValueError('Profile requires an exact lowercase APK SHA-256')
 def signature(value):
  if not isinstance(value,list) or len(value)!=3 or not all(isinstance(x,str) and x for x in value):raise ValueError('Profile signatures must be [class, name, descriptor]')
  return tuple(value)
 def mapping(name):
  result={}
  for item in profile[name]:
   if item['method'] not in ('GET','POST'):raise ValueError('Only independently verified GET/POST mappings are supported')
   key=signature(item['signature'])
   if key in result:raise ValueError('Duplicate profile signature')
   result[key]=item['method']
  return result
 global HELPERS,METHOD_HELPERS,PATH_HELPERS,ENUM,SET_METHOD,ROUTE_FIELD,METHOD_FIELD
 HELPERS=mapping('helpers');METHOD_HELPERS=mapping('method_helpers');PATH_HELPERS={signature(x)for x in profile['path_helpers']};ENUM=mapping('enum')
 SET_METHOD=signature(profile['set_method']);ROUTE_FIELD=signature(profile['route_field']);METHOD_FIELD=signature(profile['method_field'])
 return profile
load_profile(DEFAULT_PROFILE)

PARAMETER_SETTERS={
 'AQE':('(Ljava/lang/String;Ljava/lang/String;)V','string'),
 'A0F':('(Ljava/lang/String;Ljava/lang/String;)V','string'),
 'A0B':('(Ljava/lang/String;F)V','number'),
 'A0C':('(Ljava/lang/String;I)V','integer'),
 'A0D':('(Ljava/lang/String;J)V','integer'),
 'A0E':('(Ljava/lang/String;Ljava/lang/Boolean;)V','boolean'),
 'A0G':('(Ljava/lang/String;Z)V','boolean'),
 'A0H':('(Ljava/lang/String;Z)V','boolean'),
}
RESPONSE_FACTORIES={
 ('LX/02rr;','A01','(LX/0opA;LX/0Wvm;LX/0Wvm;Lcom/instagram/common/session/UserSession;I)LX/02sB;'):2,
 ('LX/02rr;','A02','(LX/0Wvm;LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;'):1,
 ('LX/02rr;','A03','(LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;'):1,
 ('LX/02rr;','A04','(LX/0Wvm;Lcom/instagram/common/session/UserSession;I)LX/02sB;'):1,
 ('LX/02rr;','A06','(LX/0Wvm;LX/0Wvm;LX/0ols;LX/05Dd;)LX/06q3;'):1,
 ('LX/02rr;','A07','(LX/0Wvm;LX/0ols;LX/05Dd;I)LX/06q3;'):1,
 ('LX/02rr;','A08','(LX/0Wvm;LX/05Dd;)LX/06q3;'):1,
}
OBJECT_STRING_HELPER=('LX/021X;','A1L','(LX/04x6;Ljava/lang/Object;Ljava/lang/String;)V')
FINALIZERS={
 ('LX/04x5;','A0K','()LX/02sG;'):'current',
 ('LX/020p;','A0K','(LX/04x5;Ljava/lang/String;)LX/02sG;'):'route',
 ('LX/0221;','A0T','(LX/04x5;)LX/02sG;'):'signed',
 ('LX/021R;','A0T','(LX/04x5;Z)LX/02sG;'):'argument',
 ('LX/021X;','A0T','(LX/04x5;Ljava/lang/String;Ljava/lang/String;)LX/02sG;'):'parameter',
 ('LX/0465;','A0N','(LX/04x5;Ljava/lang/String;Ljava/lang/String;)LX/02sG;'):'parameter-a0f',
 ('LX/0064;','A0S','(LX/04x5;Ljava/lang/String;)LX/02sG;'):'max-id',
 ('LX/0225;','A0R','(LX/04x5;Ljava/lang/String;Ljava/lang/String;)LX/02sG;'):'parameter-signed',
 ('LX/0221;','A0V','(LX/04x5;Ljava/lang/String;Ljava/lang/String;Z)LX/02sG;'):'parameter-argument',
 ('LX/0221;','A0U','(LX/04x5;LX/05BI;Ljava/lang/String;Ljava/lang/String;)LX/02sG;'):'callback-parameter',
 ('LX/0224;','A0P','(LX/04x5;Ljava/lang/String;)LX/02sG;'):'route-signed',
}

def scan(d,mid,code,include_request_fields=False):
 instructions,bounds=d.insns(code);regs={};objs={};pending=None;out=[];block=0
 def evidence(pc,op,**kw):return {'dex':d.name,'caller':sig(d.methods[mid]),'method_index':mid,'code_unit_offset':pc,'dex_byte_offset':code+16+pc*2,'operation':op,**kw}
 def obj(r,pc):
  v=regs.get(r)
  if not v or v[0]!='obj':v=('obj',f'{block}:{pc}:{r}');regs[r]=v
  return objs.setdefault(v[1],{'identity':v[1]})
 def put(o,k,v,ev):
  if include_request_fields and k in ('path','method') and k in o and o[k]!=v:o['request_fields']=[];o['observations']=[]
  o[k]=v;o[k+'_evidence']=ev
  if o.get('path') and o.get('method'):
   raw=o['path']
   if '/' in raw and not any(c.isspace() for c in raw):
    record={'path':raw if raw.startswith('/') else '/'+raw,'raw_path':raw,'method':o['method'],'confidence':'static-same-receiver-basic-block','evidence':[o['path_evidence'],o['method_evidence']],'receiver_identity':o['identity'],'basic_block_start':block,'dispatch_verified':False}
    if include_request_fields:
     record['request_fields']=o.setdefault('request_fields',[])
     if o.get('response_parser'):record['response_parser']=o['response_parser']
     if o.get('error_parser'):record['error_parser']=o['error_parser']
    out.append(record)
    if include_request_fields:o.setdefault('observations',[]).append(record)
 def parameter(o,key,method,pc,receiver):
  logical=PARAMETER_SETTERS[method[1]][1]
  presence='omitted-if-null' if method[1] in ('AQE','A0F','A0E') else 'emitted-when-setter-executes'
  serialization='one-or-zero' if method[1]=='A0H' else 'true-or-false' if method[1] in ('A0E','A0G') else 'string-value'
  o.setdefault('request_fields',[]).append({'name':key[1],'logical_type':logical,'wire_type':'string',
   'required_status':'unknown','client_presence':presence,'client_serialization':serialization,
   'encoding_status':'request parameter collection; final transport unresolved',
   'evidence':evidence(pc,'request-parameter-setter',callee=sig(method),receiver_register=receiver,key_origin=key[2])})
 for pc,op,lo,w,off in instructions:
  if pc in bounds:regs={};objs={};pending=None;block=pc
  prev=pending;pending=None
  if lo==0 and op:continue
  a=op>>8
  if lo in [0x01,0x04,0x07]:regs[a&15]=regs.get(a>>4)
  elif lo in [0x02,0x05,0x08]:regs[a]=regs.get(d.u16(off+2))
  elif lo in [0x03,0x06,0x09]:regs[d.u16(off+2)]=regs.get(d.u16(off+4))
  elif lo in [0x0a,0x0b,0x0c]:regs[a]=prev
  elif lo in [0x1a,0x1b]:
   idx=d.u16(off+2) if lo==0x1a else d.u32(off+2);regs[a]=('string',d.strings[idx],evidence(pc,'const-string',string_index=idx,value=d.strings[idx]))
  elif lo==0x62:
   f=d.fields[d.u16(off+2)];regs[a]=('http_method',ENUM[f],evidence(pc,'sget-object',field=sig(f),http_method=ENUM[f])) if f in ENUM else ('static_field',f,evidence(pc,'sget-object',field=sig(f))) if include_request_fields else None
  elif lo==0x22:regs[a]=('obj',f'{block}:{pc}:new')
  elif lo==0x5b:
   src=a&15;dst=a>>4;f=d.fields[d.u16(off+2)];v=regs.get(src)
   if f==ROUTE_FIELD:
    o=obj(dst,pc)
    if v and v[0]=='string':put(o,'path',v[1],evidence(pc,'iput-object-route',field=sig(f),receiver_register=dst,string_origin=v[2]))
    else:o.pop('path',None)
   elif f==METHOD_FIELD:
    o=obj(dst,pc)
    if v and v[0]=='http_method':put(o,'method',v[1],evidence(pc,'iput-object-http-method',field=sig(f),receiver_register=dst,enum_origin=v[2]))
    else:o.pop('method',None)
   else:
    receiver=regs.get(dst)
    if include_request_fields and receiver and receiver[0]=='obj' and receiver[1] in objs:objs[receiver[1]]['transport_safe']=False
    if v and v[0]=='obj':objs.pop(v[1],None)
  elif include_request_fields and lo in (0x59,0x5a,0x5c,0x5d,0x5e,0x5f):
   src=a&15;dst=a>>4;field=d.fields[d.u16(off+2)];receiver=regs.get(dst)
   if receiver and receiver[0]=='obj' and receiver[1] in objs:
    o=objs[receiver[1]];value=regs.get(src)
    if field==('LX/04x6;','A0U','Z') and value and value[0]=='integer' and value[1] in (0,1):
     o['envelope']='signed' if value[1] else 'plain';o['envelope_evidence']=evidence(pc,'signing-flag-assignment',field=sig(field),enabled=bool(value[1]))
    else:o['transport_safe']=False
  elif lo in range(0x6e,0x73) or lo in range(0x74,0x79):
   m=d.methods[d.u16(off+2)]
   if lo<=0x72:
    n=op>>12;tail=d.u16(off+4);args=[(tail>>(4*k))&15 for k in range(min(n,4))]+([(op>>8)&15] if n==5 else [])
   else:args=list(range(d.u16(off+4),d.u16(off+4)+a))
   if include_request_fields and m==OBJECT_STRING_HELPER and len(args)==3:
    receiver=regs.get(args[0]);value=regs.get(args[1]);key=regs.get(args[2])
    # A tracked builder used as the toString receiver has unknown virtual effects.
    if value and value[0]=='obj':objs.pop(value[1],None)
    o=objs.get(receiver[1]) if receiver and receiver[0]=='obj' else None
    if o is not None and key and key[0]=='string':
     parameter(o,key,('LX/04x6;','AQE',PARAMETER_SETTERS['AQE'][0]),pc,args[0])
     field=o['request_fields'][-1]
     field.update(client_presence='object-toString-must-succeed; null string result omitted',client_serialization='object-toString-then-string-value')
     field['evidence'].update(operation='reviewed-object-string-parameter-helper',forwarded_setter=field['evidence']['callee'],callee=sig(m))
   elif include_request_fields and m[0]=='LX/04x6;' and m[1] in PARAMETER_SETTERS and m[2]==PARAMETER_SETTERS[m[1]][0] and len(args)>=3:
    receiver=regs.get(args[0]);key=regs.get(args[1])
    if receiver and receiver[0]=='obj' and key and key[0]=='string':
     o=objs.get(receiver[1])
     if o is not None:
      parameter(o,key,m,pc,args[0])
   elif include_request_fields and m in FINALIZERS and args:
    receiver=regs.get(args[0]);o=objs.get(receiver[1]) if receiver and receiver[0]=='obj' else None
    if o:
     mode=FINALIZERS[m]
     if mode in ('route','route-signed'):
      route=regs.get(args[1]) if len(args)>1 else None
      if route and route[0]=='string':put(o,'path',route[1],evidence(pc,'verified-route-finalizer-helper',callee=sig(m)))
      else:o['transport_safe']=False
     if mode in ('signed','parameter-signed','route-signed'):o['envelope']='signed';o['envelope_evidence']=evidence(pc,'signed-finalizer-helper',callee=sig(m))
     elif mode in ('argument','parameter-argument'):
      flag_index=3 if mode=='parameter-argument' else 1
      value=regs.get(args[flag_index]) if len(args)>flag_index else None
      o['envelope']='signed' if value and value[0]=='integer' and value[1]==1 else 'plain' if value and value[0]=='integer' and value[1]==0 else None
      o['envelope_evidence']=evidence(pc,'flag-finalizer-helper',callee=sig(m))
     if mode in ('parameter','parameter-a0f','parameter-signed','parameter-argument','callback-parameter','max-id'):
      key_index=2 if mode=='callback-parameter' else 1
      key=('string','max_id',evidence(pc,'reviewed-helper-literal-key',callee=sig(m),value='max_id')) if mode=='max-id' else regs.get(args[key_index]) if len(args)>key_index else None
      if key and key[0]=='string':
       setter='A0F' if mode in ('parameter-a0f','max-id') else 'AQE'
       parameter(o,key,('LX/04x6;',setter,PARAMETER_SETTERS[setter][0]),pc,args[0])
       field=o['request_fields'][-1]
       field['evidence'].update(operation='reviewed-finalizer-parameter',forwarded_setter=field['evidence']['callee'],callee=sig(m))
     if o.get('transport_safe') and o.get('envelope') in ('plain','signed') and o.get('method') in ('GET','POST'):
      transport={'status':'client-finalization-traced','parameter_location':'query' if o['method']=='GET' else 'form-body',
       'envelope':o['envelope'],'content_type':None if o['method']=='GET' else 'application/x-www-form-urlencoded; charset=UTF-8',
       'server_requiredness':'unknown','evidence':[evidence(pc,'request-finalization',callee=sig(m)),o.get('envelope_evidence')]}
      for observation in o.get('observations',[]):observation['request_transport']=transport
     objs.pop(receiver[1],None)
   elif m in HELPERS:
    v=('obj',f'{block}:{pc}:helper');pending=v;o=objs.setdefault(v[1],{'identity':v[1]})
    if include_request_fields:o.update(envelope='plain',transport_safe=True,envelope_evidence=evidence(pc,'verified-factory-default-flags',callee=sig(m)))
    if include_request_fields and m[2].startswith('(LX/02rr;LX/0Wvm;') and len(args)>1:
     parser=regs.get(args[1])
     if parser and parser[0]=='static_field':o['response_parser']={'type':parser[1][2],'field':sig(parser[1]),'evidence':parser[2],'factory_evidence':evidence(pc,'verified-parser-factory-argument',callee=sig(m),argument_index=1)}
     if m[1]=='A0I' and o.get('response_parser'):o['error_parser']={**o['response_parser'],'role':'error'}
     elif m[1] in ('A0J','A0K'):o['error_parser']={'type':'LX/01pP;','role':'error','evidence':evidence(pc,'verified-factory-common-error-parser',callee=sig(m))}
    elif include_request_fields and m[0:2] in [('LX/0225;','A0L'),('LX/0064;','A0Q')]:
     parser_type='LX/01pP;' if m[1]=='A0L' else 'LX/03MB;'
     o['response_parser']={'type':parser_type,'field':parser_type+'->A00'+parser_type,
      'evidence':evidence(pc,'verified-helper-fixed-parser',callee=sig(m)),
      'evidence_path':'api/evidence/helper-AnonymousClass'+('0225-A0L.json' if m[1]=='A0L' else '0064-A0Q.json')}
     o['error_parser']={**o['response_parser'],'role':'error'}
    put(o,'method',HELPERS[m],evidence(pc,'verified-helper-return',callee=sig(m)))
   elif include_request_fields and m in RESPONSE_FACTORIES:
    v=('obj',f'{block}:{pc}:factory');pending=v;o=objs.setdefault(v[1],{'identity':v[1]})
    o.update(envelope='plain',transport_safe=True,envelope_evidence=evidence(pc,'verified-factory-default-flags',callee=sig(m)))
    index=RESPONSE_FACTORIES[m];parser=regs.get(args[index]) if len(args)>index else None
    if parser and parser[0]=='static_field':o['response_parser']={'type':parser[1][2],'field':sig(parser[1]),'evidence':parser[2],
     'factory_evidence':evidence(pc,'verified-parser-factory-argument',callee=sig(m),argument_index=index-1)}
    if m[1] in ('A01','A02','A06'):
     error_index=index+1;error=regs.get(args[error_index]) if len(args)>error_index else None
     if error and error[0]=='static_field':o['error_parser']={'type':error[1][2],'field':sig(error[1]),'role':'error','evidence':error[2],
      'factory_evidence':evidence(pc,'verified-parser-factory-argument',callee=sig(m),argument_index=error_index-1)}
    else:o['error_parser']={'type':'LX/01pP;','role':'error','evidence':evidence(pc,'verified-factory-common-error-parser',callee=sig(m))}
   elif m in METHOD_HELPERS and len(args)==1:
    o=obj(args[0],pc);put(o,'method',METHOD_HELPERS[m],evidence(pc,'verified-method-helper',callee=sig(m),receiver_register=args[0]))
   elif (m==('LX/04x6;','A0A','(Ljava/lang/String;)V') or m in PATH_HELPERS) and len(args)==2:
    o=obj(args[0],pc);v=regs.get(args[1])
    if v and v[0]=='string':put(o,'path',v[1],evidence(pc,'verified-path-setter',callee=sig(m),receiver_register=args[0],string_origin=v[2]))
    else:o.pop('path',None)
   elif m==SET_METHOD and len(args)==2:
    o=obj(args[0],pc);v=regs.get(args[1])
    if v and v[0]=='http_method':put(o,'method',v[1],evidence(pc,'set-http-method',callee=sig(m),receiver_register=args[0],enum_origin=v[2]))
    else:o.pop('method',None)
   else:
    for r in args:
     v=regs.get(r)
     if v and v[0]=='obj':objs.pop(v[1],None)
  elif lo in [0x4d,0x69]: # aput-object/sput-object: object escapes local tracking
   v=regs.get(a)
   if v and v[0]=='obj':objs.pop(v[1],None)
  elif lo in [0x24,0x25]:
   # Array creation may retain aliases; conservatively discard tracked object facts.
   objs.clear()
  elif lo==0x1f:pass # check-cast preserves identity
  elif lo in [0x12]:regs[a&15]=('integer',((a>>4)^8)-8) if include_request_fields else None
  elif lo in range(0x13,0x1a) or lo in [0x1c,0x20,0x21,0x23] or lo in range(0x2d,0x32) or lo in range(0x44,0x4b) or lo in range(0x52,0x59) or lo in range(0x60,0x67) or lo in range(0x7b,0xe3) or lo in [0xfe,0xff]:
   # All ordinary destination-writing formats: 12x/22c/22s use low destination nibble, remaining formats use full byte.
   dest=(a&15) if lo in [0x20,0x21,0x23] or lo in range(0x52,0x59) or lo in range(0x7b,0x90) or lo in range(0xb0,0xd8) else a
   regs[dest]=None
   # Kill adjacent wide register as well; harmless precision loss for non-wide writes.
   regs[dest+1]=None
  if lo in [0x04,0x05,0x06,0x0b]:
   wide_dest=(a&15) if lo==0x04 else d.u16(off+2) if lo==0x06 else a
   regs[wide_dest+1]=None
 return out

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apk',type=Path,default=ROOT/'apks/base.apk');parser.add_argument('--profile',type=Path,default=DEFAULT_PROFILE);parser.add_argument('--output',type=Path,default=P/'operations.json');args=parser.parse_args()
 if not args.apk.is_file():parser.error('Base APK not found. Supply --apk or acquire your own APKs; see docs/REPRODUCING.md.')
 try:profile=load_profile(args.profile)
 except (ValueError,KeyError,TypeError) as error:parser.error(str(error))
 digest=hashlib.sha256(args.apk.read_bytes()).hexdigest()
 if digest!=profile['apk_sha256']:parser.error('APK does not match the mapping profile. Use route-only extraction or trace a new profile; see docs/PORTING.md. No output written.')
 stats=collections.Counter();operations=[];errors=[];seen_methods=set();seen_fields=set()
 with zipfile.ZipFile(args.apk) as z:
  for name in z.namelist():
   if not re.fullmatch(r'classes\d*\.dex',name):continue
   d=Dex(z.read(name),name);stats['dex_files']+=1;seen_methods.update(d.methods);seen_fields.update(d.fields)
   for mid,code in d.codes():
    stats['methods_scanned']+=1
    try:operations.extend(scan(d,mid,code))
    except Exception as e:errors.append({'dex':name,'method':sig(d.methods[mid]),'error':str(e)})
   print(name,len(operations),flush=True)
 missing_methods=(set(HELPERS)|set(METHOD_HELPERS)|PATH_HELPERS|{SET_METHOD})-seen_methods;missing_fields=(set(ENUM)|{ROUTE_FIELD,METHOD_FIELD})-seen_fields
 if missing_methods or missing_fields:parser.error('Profile signatures absent from this APK. Recheck the profile; no output written. Missing methods: '+str(len(missing_methods))+'; fields: '+str(len(missing_fields)))
 unique={json.dumps(x,sort_keys=True):x for x in operations};operations=list(unique.values());stats['operation_observations']=len(operations);stats['unique_method_path_pairs']=len({(x['method'],x['path']) for x in operations});stats['errors']=len(errors)
 out={'source_apk_sha256':digest,'profile':profile['name'],'operations':operations,'stats':dict(stats),'errors':errors,'limitations':['Only same-basic-block constant strings, verified helpers and method setters; resets at every branch destination, branch fallthrough, return and handler move-exception.','Register copies preserve object identity. Register overwrites kill values. Calls receiving tracked objects invalidate configuration unless explicitly recognized.','Observations prove route and HTTP method configured on the same receiver at a point in code; later overrides, actual dispatch, server existence, authorization and success are not proven.','No string concatenation, formatting, field-loaded paths, dynamic server payloads or interprocedural recovery. No default HTTP methods assumed.','HTTP enum/helper semantics rely on REA-decompiled evidence in api/evidence. POST and GET mappings only. No network traffic generated.']}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['stats']))
if __name__=='__main__':main()
