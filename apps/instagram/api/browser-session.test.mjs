import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {requestInPage,startBrowserSession} from './browser-session.mjs';
test('browser context does not export cookies and closes on disconnect',async()=>{
 let launchOptions,contextOptions,opened,closed=false;const page={goto:async url=>{opened=url},isClosed:()=>false,evaluate:async(fn,arg)=>{assert.equal(fn,requestInPage);return {status:200,headers:{'content-type':'application/json'},body:'{}'}}};
 const browser={newContext:async options=>{contextOptions=options;return {newPage:async()=>page}},on(){},close:async()=>{closed=true}};
 const session=await startBrowserSession({launch:async options=>{launchOptions=options;return browser}});
 assert.equal(launchOptions.headless,false);assert.equal(launchOptions.chromiumSandbox,true);assert.equal(contextOptions.storageState,undefined);assert.equal(contextOptions.acceptDownloads,false);assert.equal(opened,'https://www.instagram.com/accounts/login/');
 assert.equal((await session.fetch('https://www.instagram.com/api/v1/example/')).status,200);await assert.rejects(()=>session.fetch('https://example.test/'));await session.close();assert.equal(closed,true);assert.equal(session.closed,true);
});
test('page request uses browser cookies without export and blocks redirects',async()=>{
 let options;const context={URL,AbortSignal,TextDecoder,Uint8Array,location:{origin:'https://www.instagram.com'},document:{cookie:'csrftoken=CSRF'},fetch:async(url,o)=>{options=o;return {type:'opaqueredirect',status:0}}};
 const run=arg=>vm.runInNewContext('('+requestInPage.toString()+')(arg)',{...context,arg});
 const result=await run({url:'https://www.instagram.com/api/v1/example/',method:'GET',headers:{authorization:'PRIVATE',cookie:'PRIVATE','x-local-token':'PRIVATE'},body:'ignored'});
 assert.equal(result.status,302);assert.equal(options.credentials,'same-origin');assert.equal(options.redirect,'manual');assert.equal(options.headers['x-csrftoken'],'CSRF');assert(!JSON.stringify(result).includes('CSRF'));assert(!JSON.stringify(options).includes('PRIVATE'));assert.equal(options.body,undefined);
 await assert.rejects(()=>run({url:'https://evil.test/'}));
});
