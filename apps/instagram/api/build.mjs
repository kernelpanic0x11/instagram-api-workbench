import fs from 'node:fs';
import YAML from 'yaml';
import {createHash} from 'node:crypto';
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
let operationCount=0;
for(const [path,item] of Object.entries(paths))for(const method of ['get','post','put','patch','delete','options','head','trace'])if(item[method]){
 const op=item[method];operationCount++;
 if(['post','put','patch','delete'].includes(method)&&!op.requestBody)op.requestBody={description:'Manual payload editor. This is NOT a recovered request schema; choose the encoding and fields required by this endpoint. Some endpoints require a signed_body envelope.',required:false,content:{'application/json':{schema:{},example:{}},'application/x-www-form-urlencoded':{schema:{type:'object',additionalProperties:{type:'string'}},example:{}}}};
}
const spec={openapi:'3.1.0',info:{title:'Instagram Android — extracted API evidence',version:target.version,description:'Static reconstruction from the installed Android client. Configure your session below, then use Try it out or the manual request editor. Method badges reflect recovered request configuration, not successful live execution. Unknown-method routes and GraphQL/Bloks names appear below on this page. Payloads remain partial; generic editors do not imply a recovered schema. The local proxy adds /api/v1 to relative routes unless an explicit API, GraphQL or upload prefix is present. No account action runs until you execute a request.'},servers:[{url:'/proxy',description:'Local JavaScript proxy → connected browser/Android profile (see connection panel)'}],paths:Object.fromEntries(Object.entries(paths).sort(([a],[b])=>a.localeCompare(b))),components:schemas.components,'x-source':{package:target.package,apk:'base.apk',sha256:target.sha256,identityStatus:target.identity_status||'reference snapshot',corpus:catalog.source,corpusSha256:catalog.source_sha256},'x-coverage':{...catalog.stats,pathItems:Object.keys(paths).length,documentedOperations:operationCount,limitations:catalog.limitations,excludedPathSyntax:excluded},'x-catalogs':{file:'extraction/catalog.json',graphql:catalog.entries.filter(e=>e.kind==='graphql_operation'),bloks:catalog.entries.filter(e=>e.kind==='bloks_id')}};
fs.writeFileSync(new URL('openapi.json',import.meta.url),JSON.stringify(spec,null,2)+'\n');
fs.writeFileSync(new URL('openapi.yaml',import.meta.url),YAML.stringify(spec,{lineWidth:110}));
fs.mkdirSync(new URL('vendor/',import.meta.url),{recursive:true});
for(const f of ['swagger-ui.css','swagger-ui-bundle.js','swagger-ui-standalone-preset.js','LICENSE','NOTICE','swagger-ui-bundle.js.LICENSE.txt','swagger-ui-standalone-preset.js.LICENSE.txt']){const src=new URL('node_modules/swagger-ui-dist/'+f,import.meta.url);if(fs.existsSync(src))fs.copyFileSync(src,new URL('vendor/'+f,import.meta.url));}
console.log(JSON.stringify({paths:Object.keys(paths).length,operations:operationCount,catalogEntries:catalog.entries.length,schemas:Object.keys(schemas.components.schemas).length}));
