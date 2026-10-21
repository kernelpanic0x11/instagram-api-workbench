import json,pathlib
P=pathlib.Path(__file__).resolve().parent
base=['evidence/tigon-request.json','evidence/set-method-resolved.json','evidence/build-request.json','evidence/http-finalize.json','evidence/http-request-init.json','evidence/integer-enum.json','evidence/http-method-map.json']
def ev(paths):
 out=[]
 for p in paths:
  f=P/p
  if not f.exists(): continue
  d=json.loads(f.read_text());s=d.get('structuredContent',d)
  out.append({'path':p,'evidence_id':s.get('evidence_id')})
 return out
def op(id,summary,tag,files,schema=None):
 r={'description':'Client response parser identified; HTTP status codes and wire Content-Type unverified.'}
 if schema:r['content']={'application/json':{'schema':{'$ref':'#/components/schemas/'+schema}}};r['x-media-type-status']='inferred from JSON parser'
 return {'operationId':id,'summary':summary,'tags':[tag],'description':'HTTP method traced through client request builders and integer-to-verb mapping. Relative path; server/base-path binding and authentication unresolved. Static evidence only. Payload/schema coverage is partial.','responses':{'default':r},'x-method-evidence':ev(base+files)}
ops=[]
o=op('getRecommendationStatusNudge','Recommendation status display prompt','Account status',['evidence/builder-helper.json','evidence/nudge-finalize.json','../visibility/recommendation-nudge-request.json'],'RecommendationStatusNudgeResponse');ops.append({'path':'/users/get_recommendation_status_nudge/','method':'get','operation':o})
o=op('configureToClips','Configure uploaded media as a Reel','Reels',['evidence/configure-builder.json','evidence/post-helper.json','../reels-trace/endpoint-values.json','../reels-trace/configure-request.json'],'PublishResponse');o['x-request-model']={'$ref':'#/components/schemas/ConfigureRequestTrialFields'};o['x-request-model-note']='Logical partial fields only. Transport may serialize/sign/wrap parameters; no requestBody encoding asserted.';ops.append({'path':'/media/configure_to_clips/','method':'post','operation':o})
for route,label in [('apps','Load Bloks application'),('async_action','Dispatch Bloks async action')]:
 o=op('bloks_'+route,label,'Bloks',['../visibility/bloks-http-request.json','../visibility/bloks-async-dispatch.json','../visibility/bloks-request-dispatch.json'])
 o['parameters']=[{'name':'arg1','in':'path','required':True,'schema':{'type':'string'},'description':'Bloks application identifier; dynamic legacy HTTP branch, not all Bloks calls.'}]
 o['x-request-fields']={'bloks_versioning_id':{'type':'string'},'bk_client_context':{'type':'string','description':'JSON-serialized client context'},'additional_map_entries':'Dynamic strings; not exhaustively recovered'}
 ops.append({'path':'/bloks/'+route+'/{arg1}/','method':'post','operation':o})
# Schema names verified from evidence fragment.
actual=json.loads((P/'schema-evidence/schemas.json').read_text())['components']['schemas'];print('schemas:',list(actual))
(P/'operations.json').write_text(json.dumps(ops,indent=2)+'\n')
