// A separate, non-persistent browser context. No cookie export or storageState file.
const ORIGIN='https://www.instagram.com';
export async function requestInPage({url,method,headers,body}){
 if(location.origin!=='https://www.instagram.com')throw new Error('Open Instagram in the login window first.');
 const target=new URL(url);if(target.origin!==location.origin)throw new Error('Browser requests must stay on Instagram.');
 const safe={'x-ig-app-id':'936619743392459','x-requested-with':'XMLHttpRequest'};
 for(const [k,v]of Object.entries(headers||{}))if(/^(accept|content-type|x-ig-[a-z0-9-]+|x-fb-[a-z0-9-]+|x-bloks-[a-z0-9-]+|x-requested-with)$/i.test(k))safe[k.toLowerCase()]=v;
 const csrf=document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)?.[1];if(csrf)safe['x-csrftoken']=csrf;
 const r=await fetch(target.href,{method,headers:safe,body:['GET','HEAD'].includes(method)?undefined:body,credentials:'same-origin',redirect:'manual',signal:AbortSignal.timeout(30000)});
 if(r.type==='opaqueredirect'||r.status===0)return {status:302,headers:{},body:''};
 const reader=r.body?.getReader(),chunks=[];let size=0;
 if(reader)for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>32*1024*1024){await reader.cancel();throw new Error('Response exceeds size limit.');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
 const selected={};for(const name of ['content-type','retry-after']){const value=r.headers.get(name);if(value)selected[name]=value;}
 return {status:r.status,headers:selected,body:new TextDecoder().decode(bytes)};
}
export async function startBrowserSession({launch}={}){
 let browser,stage='launch';
 try{
  if(!launch){let chromium;try{({chromium}=await import('playwright'));}catch{throw new Error('Install optional browser login support: cd api && npm ci');}launch=options=>chromium.launch(options);}
  browser=await launch({channel:'chrome',headless:false,chromiumSandbox:true});
  stage='context';const context=await browser.newContext({acceptDownloads:false,serviceWorkers:'block'});
  const page=await context.newPage();
  stage='navigation';await page.goto(ORIGIN+'/accounts/login/',{waitUntil:'domcontentloaded',timeout:30000});
  let closed=false;browser.on('disconnected',()=>{closed=true});
  return {
   get closed(){return closed||page.isClosed()},
   async fetch(url,options={}){
    if(this.closed)throw new Error('Browser login window closed.');
    const u=new URL(url);if(u.origin!==ORIGIN)throw new Error('Browser requests must stay on Instagram.');
    const result=await page.evaluate(requestInPage,{url:u.href,method:options.method||'GET',headers:options.headers||{},body:options.body?Buffer.from(options.body).toString():undefined});
    return new Response([204,205,304].includes(result.status)||options.method==='HEAD'?null:result.body,{status:result.status,headers:result.headers});
   },
   async close(){closed=true;await browser.close();}
  };
 }catch(e){await browser?.close().catch(()=>{});if(e.message?.startsWith('Install optional'))throw e;const hint=e.name==='TimeoutError'?'timeout':/net::ERR_[A-Z_]+/.exec(e.message||'')?.[0]||'browser unavailable';const error=new Error(`Browser login failed during ${stage}: ${hint}. Check Google Chrome and your connection, then try again.`);error.name='BrowserLoginError';throw error;}
}
