import {allowedAdditionalHeader} from './request-headers.mjs';
import {startBrowserSession} from './browser-session.mjs';
import {randomBytes,timingSafeEqual} from 'node:crypto';
import {expectedAccountId,checkAuthentication} from './auth-check.mjs';
export function createProxy({origin,fetchImpl=fetch,browserFactory=startBrowserSession}){
 const token=randomBytes(32).toString('hex');let credentials=null,browserSession=null;let profile='android';let expectedId=null,verification=null,generation=0,verificationRun=0;
 const hosts={android:'https://i.instagram.com',browser:'https://www.instagram.com'};
 const methods=new Set(['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS']);

 const json=(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
 async function body(req,max=10*1024*1024){let n=0,chunks=[];for await(const c of req){n+=c.length;if(n>max)throw new Error('Request body exceeds size limit');chunks.push(c)}return Buffer.concat(chunks)}
 function validToken(req){const given=req.headers['x-local-token'];return typeof given==='string'&&/^[a-f0-9]{64}$/.test(given)&&timingSafeEqual(Buffer.from(given),Buffer.from(token));}
 return async function handle(req,res){
 const path=new URL(req.url,origin).pathname;
 const connected=()=>!!credentials||!!browserSession&&!browserSession.closed;
 if(browserSession?.closed){browserSession=null;verification=null;generation++;}
 if(!path.startsWith('/api/')&&!path.startsWith('/proxy/'))return false;
 if(req.headers.host!==new URL(origin).host||(req.headers.origin&&req.headers.origin!==origin)){json(res,403,{error:'Use this application from '+origin});return true;}
 if(path==='/api/status'&&req.method==='GET'){json(res,200,{connected:connected(),transport:browserSession?'browser':'proxy',token,upstream:hosts[profile],profile,verification,credentialStorage:'Server memory only'});return true;}
 if(!validToken(req)){json(res,403,{error:'Local request token missing; reload the Swagger page.'});return true;}
 try{
 if(path==='/api/browser-login'&&req.method==='POST'){
  const version=++generation;verification=null;credentials=null;expectedId=null;await browserSession?.close();browserSession=null;
  const session=await browserFactory();if(version!==generation){await session.close();json(res,409,{error:'Connection changed while opening browser login.'});return true;}
  browserSession=session;profile='browser';json(res,200,{connected:true,transport:'browser',message:'Sign in directly in the Instagram window, then click Verify authentication. Requests use that browser session; cookies are not exported.'});return true;
 }
 if(path==='/api/connect'&&req.method==='POST'){
  const input=JSON.parse((await body(req,65536)).toString());const nextProfile=input.profile||'android';if(!Object.hasOwn(hosts,nextProfile))throw new Error('Choose browser or Android profile');const headers={};
  for(const [k,v] of Object.entries(input.headers||{})){if(!allowedAdditionalHeader(k)||typeof v!=='string'||/[\r\n]/.test(v))throw new Error('Unsupported additional header');headers[k.toLowerCase()]=v;}
  if(input.cookie){if(typeof input.cookie!=='string'||/[\r\n]/.test(input.cookie))throw new Error('Invalid cookie');headers.cookie=input.cookie.includes('=')?input.cookie:'sessionid='+input.cookie;const csrf=headers.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);if(csrf&&!headers['x-csrftoken'])headers['x-csrftoken']=csrf[1];}
  if(input.bearer){if(typeof input.bearer!=='string'||/[\r\n]/.test(input.bearer))throw new Error('Invalid bearer token');headers.authorization=/^Bearer /i.test(input.bearer)?input.bearer:'Bearer '+input.bearer;}
  if(!headers.cookie&&!headers.authorization)throw new Error('Enter a session cookie or bearer token.');
  if(nextProfile==='browser'){headers.origin=hosts.browser;headers.referer=hosts.browser+'/';headers.accept??='application/json';}
  const nextExpectedId=expectedAccountId(headers,input.expectedAccountId);
  generation++;await browserSession?.close();browserSession=null;credentials=headers;profile=nextProfile;expectedId=nextExpectedId;verification=null;generation++;json(res,200,{connected:true,profile,upstream:hosts[profile],message:'Credentials loaded locally. Instagram authentication has not yet been tested.'});return true;
 }
 if(path==='/api/disconnect'&&req.method==='POST'){credentials=null;expectedId=null;verification=null;generation++;const old=browserSession;browserSession=null;await old?.close();json(res,200,{connected:false});return true;}
 if(path==='/api/verify'&&req.method==='POST'){
  if(!connected()){json(res,401,{verified:false,error:'Connect locally before verifying authentication.'});return true;}
  const run=++verificationRun,version=generation;verification=null;
  const result=await checkAuthentication({fetchImpl:browserSession?browserSession.fetch.bind(browserSession):fetchImpl,upstream:hosts[profile],headers:{...credentials},expectedId});
  if(version!==generation||run!==verificationRun){json(res,409,{verified:false,error:'Connection changed during verification. Verify the current session again.'});return true;}
  verification=result;json(res,200,result);return true;
 }
 if(!path.startsWith('/proxy/')){json(res,404,{error:'Unknown local API'});return true;}
 if(!methods.has(req.method)){json(res,405,{error:'Unsupported HTTP method'});return true;}
 if(!connected()){json(res,401,{error:'Connect an Instagram session on this page before sending requests.'});return true;}
 let route=req.url.slice('/proxy/'.length);if(!route||route.startsWith('/')||route.includes('://')||route.includes('\\'))throw new Error('Use an Instagram relative API path.');
 if(!/^(api\/|graphql(?:\/|\?|$)|rupload_)/.test(route))route='api/v1/'+route;
 const upstream=new URL('/'+route,hosts[profile]);if(upstream.origin!==hosts[profile])throw new Error('Invalid upstream');
 const headers={...credentials};for(const [k,v] of Object.entries(req.headers))if(allowedAdditionalHeader(k)&&typeof v==='string'&&!['user-agent','accept'].includes(k))headers[k]=v;
 const payload=await body(req);const response=await (browserSession?browserSession.fetch.bind(browserSession):fetchImpl)(upstream,{method:req.method,headers,body:['GET','HEAD'].includes(req.method)||!payload.length?undefined:payload,redirect:'manual',signal:AbortSignal.timeout(30000)});
 if(response.status>=300&&response.status<400){json(res,502,{error:'Instagram returned a redirect; credentials were not forwarded to another location.',upstreamStatus:response.status});return true;}
 const chunks=[];let size=0;if(response.body)for await(const c of response.body){size+=c.length;if(size>32*1024*1024)throw new Error('Upstream response exceeds size limit');chunks.push(c)}
 const out={'Content-Type':response.headers.get('content-type')||'application/octet-stream','Cache-Control':'no-store','X-Upstream-URL':upstream.href,'X-Content-Type-Options':'nosniff','Content-Security-Policy':"sandbox; default-src 'none'"};
 for(const k of ['retry-after','x-ig-set-www-claim','ig-set-authorization']){const v=response.headers.get(k);if(v&&k==='retry-after')out[k]=v;}
 res.writeHead(response.status,out);res.end(Buffer.concat(chunks));return true;
 }catch(e){const safe=new Set(['Install optional browser login support: cd api && npm ci','Could not open browser login. Install Google Chrome and run npm ci in api, then try again.','Expected account ID must be numeric','Account IDs in the session and expected account field disagree','Choose browser or Android profile','Request body exceeds size limit','Unsupported additional header','Invalid cookie','Invalid bearer token','Enter a session cookie or bearer token.','Use an Instagram relative API path.','Invalid upstream','Upstream response exceeds size limit']);const message=e.name==='BrowserLoginError'?e.message:e.name==='TimeoutError'?'Instagram request timed out.':e.name==='SyntaxError'?'Invalid JSON.':safe.has(e.message)?e.message:'Could not complete the Instagram request.';json(res,safe.has(e.message)||e.name==='SyntaxError'?400:502,{error:message});return true;}
 };
}
