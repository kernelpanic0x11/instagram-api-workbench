import {applyRemainingReadReview,remainingReadAudit} from './remaining-read-review.mjs';
import fs from 'node:fs';
import YAML from 'yaml';
import {createHash} from 'node:crypto';
import {onlineValidationAudit} from './online-validation-audit.mjs';
import {coverageLedger} from './operation-coverage.mjs';
import {applyResponseModels} from './response-models.mjs';
import {applyRequestTransports} from './request-transports.mjs';
import {applyKeywordFilterContract} from './comment-keywords-contract.mjs';
import {applyReadRepairs} from './read-repairs.mjs';
import {applyReadValidation} from './read-validation.mjs';
import {applySharedModels} from './shared-models.mjs';
const read=p=>JSON.parse(fs.readFileSync(new URL(p,import.meta.url)));
const catalog=read('extraction/catalog.json'), schemas=read('schema-evidence/schemas.json');
const target=fs.existsSync(new URL('target.json',import.meta.url))?read('target.json'):{package:'com.instagram.android',version:'451.0.0.53.80',sha256:'4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b'};
const paths={}, excluded=[];
function normalize(raw){
 let p=raw.split(/[?#]/)[0], n=0;const mappings=[];
 p=p.replace(/\{[^{}]+\}|%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdif]|:[a-zA-Z_][a-zA-Z_0-9]*/g,original=>{const name='arg'+(++n);mappings.push({original,name});return '{'+name+'}'});
 if(!p.startsWith('/'))p='/'+p;
 if(/[{}]/.test(p.replace(/\{arg\d+\}/g,''))||/\s/.test(p))return null;
 return {path:p,mappings};
}
for(const e of catalog.entries){
 if(!['route_candidate','absolute_api_url'].includes(e.kind))continue;
 const norm=normalize(e.path);if(!norm){excluded.push(e);continue;}
 const item=paths[norm.path]??={description:'Static route candidate. HTTP method, base URL, payload, authentication and runtime use are unresolved unless stated below.', 'x-method-status':'unknown','x-evidence':[]};
 item['x-evidence'].push({...e,'x-template-mapping':norm.mappings});
 if(norm.mappings.length)item.parameters=norm.mappings.map(m=>({name:m.name,in:'path',required:true,schema:{type:'string'},description:'Neutral documentation placeholder; original token preserved in x-evidence. Server constraints unknown.'}));
}
const operations=fs.existsSync(new URL('operations.json',import.meta.url))?read('operations.json'):[];
const bulk=fs.existsSync(new URL('bulk-trace/operations.json',import.meta.url))?read('bulk-trace/operations.json').operations:[];
for(const b of bulk){
 const norm=normalize(b.path);if(!norm)continue;
 const method=b.method.toLowerCase(),path=norm.path;
 const item=paths[path]??={'x-evidence':[]};
 const op=item[method]??={operationId:'extracted_'+method+'_'+createHash('sha256').update(path).digest('hex').slice(0,12),summary:path.split('/').filter(Boolean).at(-1)?.replaceAll('_',' ')||path,tags:[path.replace(/^\/api\/v\d+\//,'/').split('/').filter(Boolean)[0]||'Other'],description:'Method and route configured on the same request-builder object in a statically traced basic block. Dispatch and server behavior unverified. Payload and authentication requirements are incomplete.',responses:{default:{description:'Raw upstream response; status codes and response schema have not been recovered.'}},'x-method-evidence':[],'x-dispatch-verified':false};
 op['x-method-evidence'].push(...b.evidence);item[method]=op;item['x-method-status']='static-configuration-traced';
 if(norm.mappings.length)item.parameters=norm.mappings.map(m=>({name:m.name,in:'path',required:true,schema:{type:'string'},description:'Recovered positional placeholder; meaning and constraints unknown.'}));
 if(b.raw_path?.includes('?')){op['x-observed-query-templates']??=[];op['x-observed-query-templates'].push(b.raw_path.split('?')[1]);}
}
for(const {path,method,operation} of operations){const item=paths[path]??={};item[method]=operation;if(operation.parameters)item.parameters=operation.parameters.filter(p=>p.in==='path');item['x-method-status']='code-traced';}
const requestFields=read('bulk-trace/request-fields.json');
if(requestFields.source_apk_sha256!==target.sha256)throw new Error('Request-field evidence differs from the target APK');
for(const entry of requestFields.operations){
 const normalized=normalize(entry.path),method=entry.method.toLowerCase();
 const operation=normalized&&paths[normalized.path]?.[method];
 if(!operation)throw new Error('Request fields reference an undocumented operation');
 operation['x-recovered-request-fields']??=[];
 for(const field of entry.fields){
  let existing=operation['x-recovered-request-fields'].find(value=>value.name===field.name);
  if(!existing){existing=structuredClone(field);operation['x-recovered-request-fields'].push(existing);}
  else{existing.logical_types=[...new Set([...existing.logical_types,...field.logical_types])];existing.client_presence_rules=[...new Set([...(existing.client_presence_rules??[]),...(field.client_presence_rules??[])])];existing.client_serializations=[...new Set([...(existing.client_serializations??[]),...(field.client_serializations??[])])];existing.evidence.push(...field.evidence);}
 }
 const name='PartialRequest_'+method+'_'+createHash('sha256').update(normalized.path).digest('hex').slice(0,12);
 schemas.components.schemas[name]={type:'object',description:'Partial logical parameter collection from same-receiver DEX tracing. Fields are serialized as strings by the client setters. Requiredness, completeness, body/query placement and signing remain unresolved. No parameter values were retained.',additionalProperties:true,
  properties:Object.fromEntries(operation['x-recovered-request-fields'].map(field=>[field.name,{type:'string',description:'Observed client parameter; server requiredness unknown. Logical source type: '+field.logical_types.join(', ')+'. Client presence: '+(field.client_presence_rules??[]).join(', ')+'. Serialization: '+(field.client_serializations??[]).join(', ')+'.','x-client-presence':field.client_presence_rules,'x-client-serialization':field.client_serializations,'x-evidence':field.evidence}]))};
 operation['x-request-model']??={$ref:'#/components/schemas/'+name};
 operation['x-request-model-note']='Partial logical fields only; final query/body encoding and signing are unresolved. Inspect x-recovered-request-fields for DEX evidence.';
}
applyResponseModels(paths,schemas.components,read('bulk-trace/response-contracts.json'),normalize,target.sha256);
const sharedContracts=read('bulk-trace/shared-contracts.json');
applySharedModels(schemas.components,sharedContracts,target.sha256);
for(const check of read('runtime-checks.json').checks){
 const operation=paths[check.path]?.[check.method];
 if(!operation||check.httpStatus!==200||check.instagramStatus!=='ok')throw new Error('Invalid live-check record');
 operation['x-live-check']={...check,scope:'One read-only authenticated response; no account data retained. Not a complete contract or continuing guarantee.'};
}
for(const check of read('runtime-error-checks.json').checks){
 const operation=paths[check.path]?.[check.method];
 if(!operation||check.credentialsSent!==false||check.rawResponseSaved!==false||check.personalValuesSaved!==false)throw new Error('Invalid anonymous probe record');
 operation['x-anonymous-response-observations']??=[];operation['x-anonymous-response-observations'].push(check);
 operation.description+='\n\n**Anonymous read observation:** HTTP '+check.httpStatus+(check.instagramStatus?', JSON status `'+check.instagramStatus+'`':'')+'. This does not establish an authenticated success or a complete error contract. Only status and field-type metadata were retained.';
}
let operationCount=0;
for(const [path,item] of Object.entries(paths))for(const method of ['get','post','put','patch','delete','options','head','trace'])if(item[method]){
 const op=item[method];operationCount++;
 if(op['x-recovered-request-fields']?.length)op.description+='\n\n**Recovered logical request fields (partial):** '+op['x-recovered-request-fields'].map(field=>'`'+field.name+'`').join(', ')+'. These client parameters are serialized as strings. Requiredness, final body/query placement, and signing remain unresolved; this list is not a complete wire schema. See x-recovered-request-fields and the linked partial request model for evidence.';
 if(['post','put','patch','delete'].includes(method)&&!op.requestBody)op.requestBody={description:'Manual payload editor. This is NOT a recovered request schema; choose the encoding and fields required by this endpoint. Some endpoints require a signed_body envelope.',required:false,content:{'application/json':{schema:{},example:{}},'application/x-www-form-urlencoded':{schema:{type:'object',additionalProperties:{type:'string'}},example:{}}}};
}
applyRequestTransports(paths,requestFields.transports??[],normalize);
for(const endpoint of ['comment','post']){
 const evidenceFile='bulk-trace/'+endpoint+'-keywords-evidence.json';
 if(fs.existsSync(new URL(evidenceFile,import.meta.url))){
  const observationFile=endpoint+'-keywords-observation.json';
  applyKeywordFilterContract(paths,schemas.components,read(evidenceFile),fs.existsSync(new URL(observationFile,import.meta.url))?read(observationFile):null,target.sha256,endpoint);
 }
}
if(fs.existsSync(new URL('read-validation-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('read-validation-results.json'),target.sha256);
if(fs.existsSync(new URL('read-repair-contracts.json',import.meta.url)) && fs.existsSync(new URL('bulk-trace/read-repair-evidence.json',import.meta.url)))applyReadRepairs(paths,read('read-repair-contracts.json'),read('bulk-trace/read-repair-evidence.json'),target.sha256);
if(fs.existsSync(new URL('read-repair-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('read-repair-results.json'),target.sha256);
if(fs.existsSync(new URL('transport-validation-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('transport-validation-results.json'),target.sha256);
if(fs.existsSync(new URL('mobile-retest-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('mobile-retest-results.json'),target.sha256);
if(fs.existsSync(new URL('additional-read-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('additional-read-results.json'),target.sha256);
if(fs.existsSync(new URL('additional-read-results.json',import.meta.url))){
 const plan=read('additional-read-plan.json');
 if(plan.source_apk_sha256!==target.sha256)throw new Error('Additional read-plan APK provenance mismatch');
 for(const check of read('additional-read-results.json').checks){
  if(check.outcome!=='observed-success')continue;
  const candidate=plan.targets.find(entry=>entry.path===check.path&&entry.method===check.method);
  const op=paths[check.path]?.get;
  if(!candidate||!op||Object.keys(candidate.query).sort().join(',')!==check.queryKeys.join(','))throw new Error('Successful read differs from its reviewed query plan');
  op['x-tested-query-example']={scope:'explicit-public-test-inputs',values:candidate.query,note:'Tested inputs, not server defaults or universal requiredness. Saved response values are omitted.'};
  op.parameters??=[];
  for(const [name,value] of Object.entries(candidate.query)){
   if(!op['x-recovered-request-fields']?.some(field=>field.name===name))throw new Error('Test query key lacks APK evidence');
   const existing=op.parameters.find(parameter=>parameter.in==='query'&&parameter.name===name);
   if(existing)existing.example=value;
   else op.parameters.push({name,in:'query',required:false,schema:{type:'string'},example:value,description:'Public input used by a successful read. Server requiredness and accepted ranges remain unknown.','x-requiredness-status':'unknown'});
  }
 }
}
if(fs.existsSync(new URL('online-read-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('online-read-results.json'),target.sha256);
if(fs.existsSync(new URL('second-read-repair-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('second-read-repair-results.json'),target.sha256);
if(fs.existsSync(new URL('remaining-read-review.json',import.meta.url))){
 const review=read('remaining-read-review.json');
 applyRemainingReadReview(paths,review,read('bulk-trace/remaining-read-evidence.json'),target.sha256);
 if(fs.existsSync(new URL('remaining-read-results.json',import.meta.url)))applyReadValidation(paths,schemas.components,read('remaining-read-results.json'),target.sha256);
 fs.writeFileSync(new URL('remaining-read-audit.json',import.meta.url),JSON.stringify(remainingReadAudit(paths,review),null,2)+'\n');
}

fs.writeFileSync(new URL('online-validation-audit.json',import.meta.url),JSON.stringify(onlineValidationAudit(paths),null,2)+'\n');
const ledger=coverageLedger(paths);
fs.writeFileSync(new URL('coverage.json',import.meta.url),JSON.stringify(ledger,null,2)+'\n');
const spec={openapi:'3.1.0',info:{title:'Instagram Android — extracted API evidence',version:target.version,description:'Static reconstruction from the installed Android client. Configure your session below, then use Try it out or the manual request editor. Method badges reflect recovered request configuration, not successful live execution. Unknown-method routes and GraphQL/Bloks names appear below on this page. Payloads remain partial; generic editors do not imply a recovered schema. The local proxy adds /api/v1 to relative routes unless an explicit API, GraphQL or upload prefix is present. No account action runs until you execute a request.'},servers:[{url:'/proxy',description:'Local JavaScript proxy → connected browser/Android profile (see connection panel)'}],paths:Object.fromEntries(Object.entries(paths).sort(([a],[b])=>a.localeCompare(b))),components:schemas.components,'x-source':{package:target.package,apk:'base.apk',sha256:target.sha256,identityStatus:target.identity_status||'reference snapshot',corpus:catalog.source,corpusSha256:catalog.source_sha256},'x-coverage':{...catalog.stats,pathItems:Object.keys(paths).length,documentedOperations:operationCount,limitations:catalog.limitations,excludedPathSyntax:excluded},'x-catalogs':{file:'extraction/catalog.json',graphql:catalog.entries.filter(e=>e.kind==='graphql_operation'),bloks:catalog.entries.filter(e=>e.kind==='bloks_id')}};
spec['x-coverage']={...spec['x-coverage'],...ledger.summary,ledger:'coverage.json'};
fs.writeFileSync(new URL('openapi.json',import.meta.url),JSON.stringify(spec,null,2)+'\n');
fs.writeFileSync(new URL('openapi.yaml',import.meta.url),YAML.stringify(spec,{lineWidth:110,aliasDuplicateObjects:false}));
fs.mkdirSync(new URL('vendor/',import.meta.url),{recursive:true});
for(const f of ['swagger-ui.css','swagger-ui-bundle.js','swagger-ui-standalone-preset.js','LICENSE','NOTICE','swagger-ui-bundle.js.LICENSE.txt','swagger-ui-standalone-preset.js.LICENSE.txt']){const src=new URL('node_modules/swagger-ui-dist/'+f,import.meta.url);if(fs.existsSync(src))fs.copyFileSync(src,new URL('vendor/'+f,import.meta.url));}
console.log(JSON.stringify({paths:Object.keys(paths).length,operations:operationCount,catalogEntries:catalog.entries.length,schemas:Object.keys(schemas.components.schemas).length}));
