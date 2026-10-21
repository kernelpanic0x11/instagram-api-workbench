import fs from 'node:fs';
import assert from 'node:assert/strict';
import SwaggerParser from '@apidevtools/swagger-parser';
import YAML from 'yaml';
const spec=JSON.parse(fs.readFileSync(new URL('openapi.json',import.meta.url))), yaml=YAML.parse(fs.readFileSync(new URL('openapi.yaml',import.meta.url),'utf8'));
assert.deepEqual(spec,yaml);
await SwaggerParser.validate(structuredClone(spec),{resolve:{external:false}});
const shapes=new Set(),ids=new Set();let operations=0;
for(const [p,item] of Object.entries(spec.paths)){
 assert(p.startsWith('/')&&!/[?#\s]/.test(p),p);
 const shape=p.replace(/\{[^}]+\}/g,'{}');assert(!shapes.has(shape),'Template collision '+p);shapes.add(shape);
 const parameters=item.parameters??[];
 for(const token of p.matchAll(/\{([^}]+)\}/g))assert(parameters.some(x=>x.name===token[1]&&x.in==='path'&&x.required===true),'Missing path parameter '+p);
 for(const method of ['get','post','put','patch','delete','options','head','trace'])if(item[method]){const op=item[method];operations++;assert(op.operationId&&!ids.has(op.operationId));ids.add(op.operationId);assert(op['x-method-evidence']?.length,'Missing method evidence');assert(op.responses);}
}
const catalog=JSON.parse(fs.readFileSync(new URL('extraction/catalog.json',import.meta.url)));
for(const e of catalog.entries){assert(e.evidence.length);for(const r of e.evidence)assert(r.dex&&Number.isInteger(r.offset)&&Number.isInteger(r.string_index));}
console.log(JSON.stringify({valid:true,jsonYamlEqual:true,paths:shapes.size,operations,catalogEntries:catalog.entries.length,externalResolution:false}));
