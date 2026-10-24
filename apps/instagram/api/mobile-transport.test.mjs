import test from 'node:test';
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {PassThrough} from 'node:stream';
import {createMobileFetch} from './mobile-transport.mjs';
function worker(reply,inspect=()=>{}){
 return (program,args,options)=>{
  assert.equal(program,'fixture-python');assert.deepEqual(args,['fixture-worker']);assert.deepEqual(options.stdio,['pipe','pipe','pipe']);
  const child=new EventEmitter();child.stdin=new PassThrough();child.stdout=new PassThrough();child.stderr=new PassThrough();child.kill=()=>{};
  const input=[];child.stdin.on('data',chunk=>input.push(chunk));
  child.stdin.on('finish',()=>queueMicrotask(()=>{inspect(JSON.parse(Buffer.concat(input)));child.stderr.write('private-fixture');child.stdout.write(JSON.stringify(reply));child.emit('close',reply.error?1:0);}));
  return child;
 };
}
test('mobile worker receives exact credentials/body through stdin and returns decoded bytes',async()=>{
 const fetch=createMobileFetch({python:'fixture-python',worker:'fixture-worker',spawnImpl:worker({status:200,headers:{'content-type':'application/json'},body:Buffer.from('{"status":"ok"}').toString('base64')},request=>{
  assert.equal(request.headers.authorization,'private-fixture');assert.equal(request.method,'POST');assert.equal(Buffer.from(request.body,'base64').toString(),'a=b');
 })});
 const response=await fetch('https://i.instagram.com/api/v1/example/',{method:'POST',headers:{Authorization:'private-fixture'},body:'a=b'});
 assert.equal(response.status,200);assert.deepEqual(await response.json(),{status:'ok'});
});
test('mobile worker refuses foreign hosts and hides worker diagnostics',async()=>{
 const fetch=createMobileFetch({python:'fixture-python',worker:'fixture-worker',spawnImpl:worker({error:'private-fixture'})});
 await assert.rejects(()=>fetch('https://untrusted.invalid/'),/destination/);
 await assert.rejects(()=>fetch('https://i.instagram.com/api/v1/example/'),error=>!error.message.includes('private-fixture')&&/failed/.test(error.message));
});
