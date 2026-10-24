import test from 'node:test';
import assert from 'node:assert/strict';
import {Readable} from 'node:stream';
import {createProxy} from './proxy.mjs';
const origin='http://127.0.0.1:8766';
function fixture(fetchImpl=async()=>new Response('{"ok":true}',{headers:{'content-type':'application/json'}}),browserFactory){
 const handle=createProxy({origin,fetchImpl,browserFactory});
 async function request(url,{method='GET',headers={},body}={}){
  const req=Readable.from(body===undefined?[]:[Buffer.from(typeof body==='string'?body:JSON.stringify(body))]);
  Object.assign(req,{url,method,headers:{host:'127.0.0.1:8766',origin,...headers}});
  const res={status:0,headers:{},writeHead(status,headers){this.status=status;this.headers=headers;return this},end(data){this.text=data===undefined?'':data.toString()}};
  res.handled=await handle(req,res);res.json=()=>JSON.parse(res.text);return res;
 }
 async function connect(input={cookie:'sessionid=PRIVATE; csrftoken=CSRF'}){
  const token=(await request('/api/status')).json().token;
  const r=await request('/api/connect',{method:'POST',headers:{'x-local-token':token},body:input});assert.equal(r.status,200);return token;
 }
 return {request,connect};
}
test('preserves method, body, query, credentials; only safe response headers escape',async()=>{
 let observed;const f=fixture(async(url,options)=>{observed={url,options};return new Response('{"detail":"upstream denied"}',{status:403,headers:{'content-type':'application/json','set-cookie':'sessionid=SECRET','ig-set-authorization':'SECRET','retry-after':'7'}})});
 const token=await f.connect();const r=await f.request('/proxy/media/123/edit/?media_type=2&x=a%2Fb',{method:'POST',headers:{'x-local-token':token,'content-type':'application/json','x-ig-app-id':'APP','authorization':'ATTACK','cookie':'ATTACK'},body:'{"caption":"hello"}'});
 assert.equal(observed.url.href,'https://i.instagram.com/api/v1/media/123/edit/?media_type=2&x=a%2Fb');assert.equal(observed.options.method,'POST');assert.equal(observed.options.body.toString(),'{"caption":"hello"}');assert.equal(observed.options.headers.cookie,'sessionid=PRIVATE; csrftoken=CSRF');assert.equal(observed.options.headers['x-csrftoken'],'CSRF');assert.equal(observed.options.headers['x-local-token'],undefined);assert.equal(observed.options.headers.authorization,undefined);assert.equal(observed.options.redirect,'manual');assert.equal(r.status,403);assert.equal(r.json().detail,'upstream denied');assert.equal(r.headers['retry-after'],'7');assert(!JSON.stringify(r.headers).includes('SECRET'));
});
test('prefixing preserves explicit API, GraphQL, and rupload paths',async()=>{
 const urls=[];const f=fixture(async(u,o)=>{urls.push(u.href);assert.equal(o.body,undefined);return new Response('ok')});const token=await f.connect({bearer:'TOKEN'});
 for(const route of ['api/v1/feed/timeline/','graphql?doc_id=123','rupload_igphoto/123','feed/timeline/'])assert.equal((await f.request('/proxy/'+route,{headers:{'x-local-token':token}})).status,200);
 assert.deepEqual(urls,['https://i.instagram.com/api/v1/feed/timeline/','https://i.instagram.com/graphql?doc_id=123','https://i.instagram.com/rupload_igphoto/123','https://i.instagram.com/api/v1/feed/timeline/']);
});
test('status and disconnect do not reveal or retain credentials',async()=>{
 let calls=0;const f=fixture(async()=>{calls++;return new Response('ok')});const token=await f.connect({bearer:'TOP_SECRET'});const status=await f.request('/api/status');assert.equal(status.json().connected,true);assert(!status.text.includes('TOP_SECRET'));assert.equal(status.headers['Cache-Control'],'no-store');assert.equal((await f.request('/api/disconnect',{method:'POST',headers:{'x-local-token':token}})).json().connected,false);assert.equal((await f.request('/api/status')).json().connected,false);assert.equal((await f.request('/proxy/feed/',{headers:{'x-local-token':token}})).status,401);assert.equal(calls,0);
});
test('rejects foreign origin/host, missing and Unicode tokens without throwing',async()=>{
 const f=fixture();const token=await f.connect();
 for(const headers of [{origin:'https://evil.test'},{host:'evil.test'},{'x-local-token':'bad'},{'x-local-token':'é'.repeat(64)}]){
  const r=await f.request('/api/disconnect',{method:'POST',headers:{'x-local-token':token,...headers}});assert.equal(r.status,403);
 }
 assert.equal((await f.request('/api/connect',{method:'POST',body:{cookie:'secret'}})).status,403);
});
test('never follows redirects or accepts absolute/authority upstream URLs',async()=>{
 let calls=0;const f=fixture(async(u,o)=>{calls++;assert.equal(u.origin,'https://i.instagram.com');assert.equal(o.redirect,'manual');return new Response(null,{status:302,headers:{location:'https://evil.test/?token=TOP_SECRET'}})});const token=await f.connect();
 for(const route of ['/evil.test/a','https://evil.test/a','\\evil.test/a'])assert.equal((await f.request('/proxy/'+route,{headers:{'x-local-token':token}})).status,400);
 assert.equal(calls,0);const r=await f.request('/proxy/feed/',{headers:{'x-local-token':token}});assert.equal(r.status,502);assert.equal(calls,1);assert(!r.text.includes('TOP_SECRET'));
});
test('invalid JSON and transport failure give useful non-sensitive errors',async()=>{
 const f=fixture(async()=>{throw new Error('fetch failed')});const token=await f.connect();const r=await f.request('/proxy/feed/',{headers:{'x-local-token':token}});assert.match(r.json().error,/(reach Instagram|complete the Instagram request)/i);
 const bad=await f.request('/api/connect',{method:'POST',headers:{'x-local-token':token},body:'{'});assert.equal(bad.status,400);assert.match(bad.json().error,/JSON/);
});
test('arbitrary transport error text cannot disclose credentials',async()=>{
 const f=fixture(async()=>{throw new Error('upstream failure with TOP_SECRET')});const token=await f.connect({bearer:'TOP_SECRET'});const r=await f.request('/proxy/feed/',{headers:{'x-local-token':token}});assert(!r.text.includes('TOP_SECRET'));
});
test('browser profile uses only the selected fixed host and preserves encoded sessionid',async()=>{
 let observed;const f=fixture(async(url,options)=>{observed={url,options};return new Response('<html>not found</html>',{status:404,headers:{'content-type':'text/html'}})});
 const token=await f.connect({profile:'browser',cookie:'1%3AFAKE%3A17',headers:{'User-Agent':'synthetic-browser'}});
 const r=await f.request('/proxy/api/v1/example/',{headers:{'x-local-token':token}});
 assert.equal(observed.url.href,'https://www.instagram.com/api/v1/example/');assert.equal(observed.options.headers.cookie,'sessionid=1%3AFAKE%3A17');assert.equal(observed.options.headers['user-agent'],'synthetic-browser');assert.equal(observed.options.headers.origin,'https://www.instagram.com');assert.equal(r.status,404);assert.match(r.headers['Content-Security-Policy'],/sandbox/);
 const s=(await f.request('/api/status')).json();assert.equal(s.profile,'browser');assert.equal(s.upstream,'https://www.instagram.com');assert(!JSON.stringify(s).includes('FAKE'));
 const bad=await f.request('/api/connect',{method:'POST',headers:{'x-local-token':token},body:{profile:'https://evil.test',cookie:'synthetic'}});assert.equal(bad.status,400);assert.equal((await f.request('/api/status')).json().profile,'browser');
});
test('verification belongs to current connection and disconnect clears it',async()=>{
 const f=fixture(async()=>new Response(JSON.stringify({status:'ok',user:{pk:'123',username:'fixture'}}),{headers:{'content-type':'application/json'}}));const token=await f.connect({profile:'android',cookie:'ds_user_id=123; sessionid=FAKE'});
 const r=await f.request('/api/verify',{method:'POST',headers:{'x-local-token':token}});assert.equal(r.json().verified,true);assert.equal((await f.request('/api/status')).json().verification.account.id,'123');
 await f.request('/api/disconnect',{method:'POST',headers:{'x-local-token':token}});assert.equal((await f.request('/api/status')).json().verification,null);
});
test('disconnect while verifying prevents stale authentication success',async()=>{
 let finish;const f=fixture(()=>new Promise(resolve=>{finish=resolve}));const token=await f.connect({cookie:'ds_user_id=123; sessionid=FAKE'});const pending=f.request('/api/verify',{method:'POST',headers:{'x-local-token':token}});
 await f.request('/api/disconnect',{method:'POST',headers:{'x-local-token':token}});finish(new Response(JSON.stringify({status:'ok',user:{pk:'123',username:'fixture'}}),{headers:{'content-type':'application/json'}}));const r=await pending;assert.equal(r.status,409);assert.equal(r.json().verified,false);assert.equal((await f.request('/api/status')).json().verification,null);
});

test('browser login verifies and executes through browser transport; disconnect closes it',async()=>{
 let closed=false,calls=0;const browser={get closed(){return closed},close:async()=>{closed=true},fetch:async(url,options)=>{calls++;assert.equal(new URL(url).origin,'https://www.instagram.com');assert(!options.headers.cookie);return new Response(JSON.stringify({status:'ok',form_data:{username:'fixture',email:'PRIVATE',phone_number:'PRIVATE'}}),{headers:{'content-type':'application/json'}})}};
 const f=fixture(async()=>{throw new Error('Node transport should not run')},async()=>browser),token=(await f.request('/api/status')).json().token;
 assert.equal((await f.request('/api/browser-login',{method:'POST',headers:{'x-local-token':token}})).status,200);assert.equal((await f.request('/api/status')).json().transport,'browser');
 const verification=await f.request('/api/verify',{method:'POST',headers:{'x-local-token':token}});assert.equal(verification.json().verified,true);assert(!verification.text.includes('PRIVATE'));
 assert.equal((await f.request('/proxy/api/v1/accounts/edit/web_form_data/',{headers:{'x-local-token':token}})).status,200);assert.equal(calls,2);
 await f.request('/api/disconnect',{method:'POST',headers:{'x-local-token':token}});assert.equal(closed,true);assert.equal((await f.request('/api/status')).json().connected,false);
});
test('disconnect during browser launch closes the stale browser',async()=>{
 let resolve,closed=false;const f=fixture(undefined,()=>new Promise(r=>{resolve=r})),token=(await f.request('/api/status')).json().token;
 const pending=f.request('/api/browser-login',{method:'POST',headers:{'x-local-token':token}});await new Promise(r=>setImmediate(r));
 await f.request('/api/disconnect',{method:'POST',headers:{'x-local-token':token}});resolve({close:async()=>{closed=true}});
 assert.equal((await pending).status,409);assert.equal(closed,true);assert.equal((await f.request('/api/status')).json().connected,false);
});

test('preserves SDK session and integrity headers without allowing host or transport framing overrides',async()=>{
 const captured=[];const f=fixture(async(url,options)=>{captured.push(options);return new Response('{"status":"ok"}',{headers:{'content-type':'application/json'}})});
 const token=await f.connect({bearer:'synthetic-token',headers:{'IG-U-DS-USER-ID':'123','IG-U-RUR':'synthetic-route','X-Meta-Usdid':'synthetic-integrity','Accept-Language':'en-US','X-Tigon-Is-Retry':'False'}});
 await f.request('/proxy/notifications/get_notification_settings/?enable_ig_new_settings=false',{headers:{'x-local-token':token}});
 assert.equal(captured[0].headers['ig-u-rur'],'synthetic-route');
 assert.equal(captured[0].headers['x-meta-usdid'],'synthetic-integrity');
 assert.equal(captured[0].headers['accept-language'],'en-US');
 for(const name of ['Host','Connection','Content-Length','Transfer-Encoding','Accept-Encoding','Authorization','Cookie']){
  const result=await f.request('/api/connect',{method:'POST',headers:{'x-local-token':token},body:{bearer:'synthetic',headers:{[name]:'synthetic'}}});
  assert.equal(result.status,400);
 }
});
