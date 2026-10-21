import test from 'node:test';
import assert from 'node:assert/strict';
import {expectedAccountId,checkAuthentication,ACCOUNT_PATH} from './auth-check.mjs';
const headers={cookie:'sessionid=123%3AFAKE; ds_user_id=123'},upstream='https://i.instagram.com';
const verify=fetchImpl=>checkAuthentication({fetchImpl,upstream,headers,expectedId:'123'});
const reply=(data,status=200,contentType='application/json')=>new Response(typeof data==='string'?data:JSON.stringify(data),{status,headers:{'content-type':contentType}});
test('extracts expected identity without altering encoded cookie; rejects conflicts',()=>{
 assert.equal(expectedAccountId(headers),'123');assert.equal(expectedAccountId({cookie:'sessionid=123%3AFAKE'}),'123');assert.equal(expectedAccountId({authorization:'Bearer FAKE'},'123'),'123');assert.throws(()=>expectedAccountId(headers,'456'),/disagree/);assert.equal(expectedAccountId({authorization:'Bearer FAKE'}),null);
});
test('proof requires fixed current-account GET, JSON status ok, ID match and username',async()=>{
 const result=await verify(async(url,opts)=>{assert.equal(url,upstream+ACCOUNT_PATH);assert.equal(opts.method,'GET');assert.equal(opts.redirect,'manual');assert.equal(opts.headers.cookie,headers.cookie);return reply({status:'ok',user:{pk:123,username:'fixture',email:'private@example.test',phone_number:'private'}})});
 assert.equal(result.verified,true);assert.deepEqual(result.account,{id:'123',username:'fixture'});assert(!JSON.stringify(result).includes('private'));
});
test('generic 200, public-profile JSON, mismatched identity, login and challenge never verify',async()=>{
 for(const data of [{status:'ok'},{status:'ok',data:{user:{pk:123,username:'fixture'}}},{status:'ok',user:{pk:456,username:'other'}},{status:'fail',user:{pk:123,username:'fixture'}},{status:'ok',user:{pk:123,username:'fixture'},challenge:{}},{status:'ok',user:{pk:123}}])assert.equal((await verify(async()=>reply(data))).verified,false);
});
test('HTML, redirects, 401, 404, malformed JSON and network failure never verify',async()=>{
 for(const r of [reply('<html>login</html>',200,'text/html'),reply('{}',302),reply('{}',401),reply('{}',404),reply('invalid')])assert.equal((await verify(async()=>r)).verified,false);
 assert.equal((await verify(async()=>{throw new Error('SECRET')})).verified,false);
});
test('opaque tokens can authenticate through current-account identity without a prior account ID',async()=>{
 let called=false;const r=await checkAuthentication({upstream,headers:{authorization:'Bearer FAKE'},expectedId:null,fetchImpl:async()=>{called=true;return reply({status:'ok',user:{pk:'123',username:'fixture'}})}});assert.equal(r.verified,true);assert.equal(called,true);assert.equal(r.identityMatch,'not_requested');assert.deepEqual(r.account,{id:'123',username:'fixture'});
});

test('redirect diagnostics distinguish login, challenge and unknown without following or exposing locations',async()=>{
 for(const [location,reason] of [
  ['/accounts/login/?next=SECRET','redirect_login'],
  ['https://www.instagram.com/challenge/SECRET/','redirect_challenge'],
  ['/checkpoint/SECRET/','redirect_challenge'],
  ['https://example.test/accounts/login/?token=SECRET','redirect_unverified'],
  ['https://www.instagram.com.evil.test/accounts/login/SECRET','redirect_unverified'],
  ['/other/SECRET','redirect_unverified'],
  ['', 'redirect_unverified']
 ]){
  let calls=0;const result=await verify(async()=>{calls++;return new Response(null,{status:302,headers:location?{location}:{}})});
  assert.equal(calls,1);assert.equal(result.verified,false);assert.equal(result.reason,reason);assert.equal(result.upstreamStatus,302);assert(!JSON.stringify(result).includes('SECRET'));
 }
});

test('follows only bounded same-origin canonical current-account redirects',async()=>{
 let calls=0;const result=await verify(async(url)=>{calls++;if(calls===1)return new Response(null,{status:302,headers:{location:'/api/v1/accounts/current_user/'}});assert.equal(url,upstream+'/api/v1/accounts/current_user/');return reply({status:'ok',user:{pk:123,username:'fixture'}})});
 assert.equal(result.verified,true);assert.equal(calls,2);
 for(const location of ['https://www.instagram.com'+ACCOUNT_PATH,'http://www.instagram.com'+ACCOUNT_PATH,'https://www.instagram.com:444'+ACCOUNT_PATH,'/api/v1/accounts/current_user/?token=SECRET','/']){
  let calls=0;const result=await verify(async()=>{calls++;return new Response(null,{status:302,headers:{location}})});assert.equal(result.verified,false);assert.equal(calls,1);assert(!JSON.stringify(result).includes('SECRET'));
 }
 let loops=0;const loop=await verify(async()=>{loops++;return new Response(null,{status:302,headers:{location:'/api/v1/accounts/current_user/'}})});assert.equal(loop.verified,false);assert.equal(loops,2);
});

test('browser verifies private settings response and never returns personal fields or claims an ID match',async()=>{
 const run=data=>checkAuthentication({upstream:'https://www.instagram.com',headers,expectedId:'123',fetchImpl:async(url,options)=>{assert.equal(url,'https://www.instagram.com/api/v1/accounts/edit/web_form_data/');assert.equal(options.headers['x-ig-app-id'],'936619743392459');return reply(data)}});
 const result=await run({status:'ok',form_data:{username:'fixture',email:'SECRET',phone_number:'SECRET',birthday:'SECRET'}});assert.equal(result.verified,true);assert.deepEqual(result.account,{username:'fixture'});assert.equal(result.identityMatch,'unavailable');assert(!JSON.stringify(result).includes('SECRET'));
 for(const data of [{status:'ok',user:{username:'fixture'}},{status:'ok',form_data:{username:'fixture'}},{status:'fail',form_data:{username:'fixture',email:'',phone_number:''}}])assert.equal((await run(data)).verified,false);
});
