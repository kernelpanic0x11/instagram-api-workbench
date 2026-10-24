import fs from 'node:fs';
import assert from 'node:assert/strict';
import SwaggerParser from '@apidevtools/swagger-parser';
import YAML from 'yaml';
import {coverageLedger} from './operation-coverage.mjs';
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
const ledger=JSON.parse(fs.readFileSync(new URL('coverage.json',import.meta.url)));
assert.deepEqual(coverageLedger(spec.paths),ledger,'Coverage ledger differs from Swagger operations');
assert.equal(ledger.summary.documentedOperations,operations);
for(const {path,method,fields} of ledger.operations)if(fields.length){
 const op=spec.paths[path][method];
 assert(op['x-request-model']);
 assert(op['x-recovered-request-fields'].every(field=>field.evidence.length&&field.required_status==='unknown'));
}
for(const {path,method,responseFields,responseParserBound} of ledger.operations){
 const operation=spec.paths[path][method];
 if(responseFields.length){
  assert(responseParserBound,'Recovered response fields lack a parser binding');
  assert(operation['x-recovered-response-fields'].every(field=>field.evidence.length&&field.evidence.every(evidence=>Number.isInteger(evidence.dex_byte_offset))));
 }
}
for(const e of catalog.entries){assert(e.evidence.length);for(const r of e.evidence)assert(r.dex&&Number.isInteger(r.offset)&&Number.isInteger(r.string_index));}
console.log(JSON.stringify({valid:true,jsonYamlEqual:true,paths:shapes.size,operations,catalogEntries:catalog.entries.length,externalResolution:false}));
