from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
sources={}
def ev(path,needle):
 t=(R/path).read_text();lines=t.splitlines();n=next(i+1 for i,l in enumerate(lines) if needle in l)
 sources[path]={'sha256':hashlib.sha256(t.encode()).hexdigest()}
 return {'path':path,'line':n,'excerpt':lines[n-1].strip()}
def prop(path,needle,typ=None,desc='',confidence='observed'):
 p={'description':desc,'x-evidence':[ev(path,needle)],'x-confidence':confidence}
 if typ:p['type']=typ
 return p
def obj(desc,properties,**kw):return {'type':'object','description':desc,'properties':properties,'additionalProperties':True,**kw}
s={}
p='visibility/nudge-response-parser.java'
s['RecommendationStatusNudgeResponse']=obj('Partial client response model. The parser throws if show_recommendation_status_nudge is absent or unresolved; this is a display prompt flag, not a reach score.',{'show_recommendation_status_nudge':prop(p,'boolA0c = C0C9W.A0c','boolean','Client Boolean is unboxed; missing value causes parser failure.')},required=['show_recommendation_status_nudge'])
p='visibility/restriction-parser.java';t=(R/p).read_text();fields={}
for m in re.finditer(r'str.equals\("([^"]+)"\)([^\n]*)',t):
 name,tail=m.groups();needle='str.equals("'+name+'")'
 if 'strA' in tail and 'C01yt.A07' in tail:
  fields[name]=prop(p,needle,['string','null'],'Parsed to Java String; null values are ignored. No timestamp/URI format or requiredness inferred.')
 else:
  fields[name]=prop(p,needle,None,'Field recognized by common response parser; delegated parser or accessor wire type not independently verified.')
fields['_messages']['type']='array';fields['_messages']['items']={};fields['_messages']['description']='Array token explicitly checked; non-null elements delegated to X.0Kbr parser. Element schema unresolved.'
s['CommonRestrictionResponseFields']=obj('Partial common response/error fields. General enforcement and challenges, not exclusively recommendations. Fields are not claimed present on every endpoint.',fields,**{'x-unknowns':['Obfuscated field names and symbolic constants not independently resolved are omitted.','A12 boolean-like accessors were not separately decoded; corresponding property types intentionally omitted.','Nested consent_data/challenge/message schemas and server requiredness are unresolved.']})
p='reels-trace/publish-response-parser.java';fields={}
for name in ['max_cutout_sticker_limit','cooldown_time_in_seconds','retry_entire_upload_flow','media','medias','posts']:
 fields[name]=prop(p,'strA08.equals("'+name+'")',None,'Recognized by client publish-response parser; optional presence in this parser.')
for name in ['medias','posts']:
 fields[name].update(type='array',items={});fields[name]['description']='JSON array token explicitly checked; element parser schema unresolved.'
fields['media']['description']='Delegated to Media parser. Nested schema and permitted wire token types unresolved.'
fields['max_cutout_sticker_limit']['x-unknowns']=['X.0025.A0H helper return type not independently decoded.']
fields['cooldown_time_in_seconds']['x-unknowns']=['X.0025.A0H helper return type not independently decoded; numeric-sounding name alone does not establish type.']
fields['retry_entire_upload_flow']['x-unknowns']=['X.0025.A0D helper return type not independently decoded; boolean-sounding name alone does not establish type.']
s['PublishResponse']=obj('Partial response parsed by X.0ZMX into X.0XvS. Unknown fields delegated to common response parser X.01pP.A01. No server-required fields established.',fields,**{'x-evidence':[ev('reels-trace/configure-response.java','C0ZMX.A00.parseFromJsonParser')],'x-unknowns':['Symbolic comment field constant not independently resolved; omitted.','Obfuscated field X.0005.A00(904) omitted.','No HTTP status codes or auth requirements established.']})
p='reels-trace/trial-params.java';gp=prop(p,'"graduation_strategy"','string','Serializer writes enum.toString(); emitted unconditionally when serializing this object. Server requiredness unknown.')
gp['x-candidate-enum-values']=['manual','ss_performance','time_limit','UNSET_OR_UNRECOGNIZED_ENUM_VALUE'];gp['x-evidence'].append(ev('reels-trace/trial-strategy-values.smali','const-string v1, "manual"'));gp['x-unknowns']=['Enum constructor strings observed; toString body not available in saved sources, so a closed wire enum is not asserted.']
s['TrialParams']=obj('Serialized inner JSON object from X.0ROZ.A00. Request builder serializes this to text before attaching trial_params.',{'graduation_strategy':gp},**{'x-client-emits':['graduation_strategy']})
p='reels-trace/configure-request.java';tp=prop(p,'c02sBA00.AQU(C005P.A00(48), string17);','string','JSON-serialized TrialParams text is passed to request builder AQU. Final media type and transport encoding not established here.')
tp['contentMediaType']='application/json';tp['contentSchema']={'$ref':'#/components/schemas/TrialParams'};tp['x-evidence'].append(ev('reels-trace/upload/NOTES.txt','X.005P.A00(48) maps trial_params'))
s['ConfigureRequestTrialFields']=obj('Partial request-builder fields only; do not treat this as the complete configure payload.',{'trial_params':tp})
result={'components':{'schemas':s},'x-notes':['OpenAPI 3.1-compatible schema fragment; all objects permit unobserved fields.','Static client observations only. No API calls, live verification, authentication claims, methods, or HTTP statuses supplied.','Client decoded value types can differ from permissive parser wire coercions. Null explicitly allowed for ignored String fields.','Only recommendation nudge requiredness is asserted, because its parser throws.','trial-serializer.java is the entire draft persistence serializer; it is not treated as a network request schema.'],'x-source-files':sources}
(P/'schemas.json').write_text(json.dumps(result,indent=2)+'\n')
print(len(s),'schemas;',sum(len(x.get('properties',{})) for x in s.values()),'properties')
