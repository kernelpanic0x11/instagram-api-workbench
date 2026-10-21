// Fixed current-account endpoint; never substitute a public profile lookup.
export const BROWSER_ACCOUNT_PATH='/api/v1/accounts/edit/web_form_data/';
export const ACCOUNT_PATH='/api/v1/accounts/current_user/?edit=true';
function numericId(value){if(typeof value==='number'&&!Number.isSafeInteger(value))return null;return /^(?:[1-9]\d*)$/.test(String(value??''))?String(value):null;}
export function expectedAccountId(headers,explicit){
 const candidates=[];if(explicit){const id=numericId(explicit);if(!id)throw new Error('Expected account ID must be numeric');candidates.push(id);}
 const cookies=Object.fromEntries((headers.cookie||'').split(';').map(x=>{const i=x.indexOf('=');return i<0?[]:[x.slice(0,i).trim(),x.slice(i+1).trim()]}).filter(x=>x.length===2));
 if(cookies.ds_user_id){let v;try{v=decodeURIComponent(cookies.ds_user_id)}catch{}const id=numericId(v);if(id)candidates.push(id);}
 if(cookies.sessionid){let v;try{v=decodeURIComponent(cookies.sessionid)}catch{}const id=v?.match(/^([1-9]\d*):/)?.[1];if(id)candidates.push(id);}
 if(headers['ig-intended-user-id']){const id=numericId(headers['ig-intended-user-id']);if(id)candidates.push(id);}
 if(new Set(candidates).size>1)throw new Error('Account IDs in the session and expected account field disagree');
 return candidates[0]||null;
}
export async function checkAuthentication({fetchImpl,upstream,headers,expectedId}){
 const browser=upstream==='https://www.instagram.com',accountPath=browser?BROWSER_ACCOUNT_PATH:ACCOUNT_PATH;
 const checkedAt=new Date().toISOString(),base={verified:false,checkedAt,endpoint:upstream+accountPath};
 if(browser)headers={'x-ig-app-id':'936619743392459','x-requested-with':'XMLHttpRequest',...headers};
 try{
  let requestUrl=base.endpoint,r;const visited=new Set();
  for(let hop=0;hop<3;hop++){
  visited.add(requestUrl);
  r=await fetchImpl(requestUrl,{method:'GET',headers:{...headers,accept:'application/json','cache-control':'no-cache'},redirect:'manual',signal:AbortSignal.timeout(30000)});
  const failed={...base,upstreamStatus:r.status};
  if(r.status>=300&&r.status<400){
   // Only follow canonical redirects to this same-origin current-account route.
   const location=r.headers.get('location');let target;
   try{if(location)target=new URL(location,requestUrl);}catch{}
   await r.body?.cancel();
   const trusted=target?.protocol==='https:'&&['www.instagram.com','i.instagram.com','instagram.com'].includes(target.hostname)&&!target.port&&!target.username&&!target.password;
   const sameAccount=trusted&&target.origin===new URL(base.endpoint).origin&&target.pathname.replace(/\/$/,'')===accountPath.split('?')[0].replace(/\/$/,'')&&[...target.searchParams].every(([k,v])=>k==='edit'&&v==='true');
   if(sameAccount&&hop<2&&!visited.has(target.href)){requestUrl=target.href;continue;}
   const knownPaths=new Set(['/','/accounts/login/','/accounts/onetap/','/accounts/suspended/','/accounts/disabled/','/challenge/','/checkpoint/','/api/v1/accounts/current_user/','/api/v1/accounts/current_user']);
   const destination=trusted?target.origin+(knownPaths.has(target.pathname)?target.pathname:'/[…redacted path…]'):null;
   if(trusted&&/^\/accounts\/login(?:\/|$)/.test(target.pathname))return {...failed,reason:'redirect_login',message:'Instagram redirected this request to login. This request was not authenticated. Check that the selected profile matches your credentials and reconnect with a current session from your logged-in browser.'};
   if(trusted&&/^\/(?:challenge|checkpoint)(?:\/|$)/.test(target.pathname))return {...failed,reason:'redirect_challenge',message:'Instagram redirected this request to an account challenge. Complete it directly in Instagram, then reconnect and verify again.'};
   return {...failed,reason:'redirect_unverified',message:`Instagram returned HTTP ${r.status} with ${trusted?'a redirect to '+destination:target?'a redirect outside the approved Instagram HTTPS hosts':'no usable redirect destination'}. The current-account endpoint did not confirm authentication. No credentials were forwarded to that destination. Check the selected profile and session; a redirect alone cannot establish whether the credentials are valid.`};
  }
  break;
  }
  const failed={...base,upstreamStatus:r.status};
  if(r.status!==200){await r.body?.cancel();return {...failed,reason:'upstream_rejected',message:`Instagram returned HTTP ${r.status}; authentication is not verified.`};}
  if(!/\bapplication\/(?:[\w.-]+\+)?json\b/i.test(r.headers.get('content-type')||'')){await r.body?.cancel();return {...failed,reason:'non_json',message:'Instagram did not return account JSON; authentication is not verified.'};}
  const chunks=[];let size=0;for await(const chunk of r.body){size+=chunk.length;if(size>1024*1024)throw new Error('response too large');chunks.push(chunk);}
  const data=JSON.parse(Buffer.concat(chunks).toString());
  if(data.status!=='ok'||data.challenge||data.checkpoint_url||data.message==='login_required')return {...failed,reason:'login_or_challenge',message:'Instagram did not confirm an authenticated current account.'};
  if(browser){
   const form=data.form_data;
   if(!form||typeof form.username!=='string'||!form.username.trim()||!Object.hasOwn(form,'email')||!Object.hasOwn(form,'phone_number'))return {...failed,reason:'missing_identity',message:'Instagram did not return authenticated account-settings data.'};
   return {...base,verified:true,upstreamStatus:r.status,account:{username:form.username},identityMatch:'unavailable',message:`Authenticated as @${form.username}. Instagram accepted the session for the private account-settings GET. This response does not provide a numeric account ID, so an expected ID cannot be checked here.`};
  }
  const user=data.user,id=numericId(user?.pk??user?.pk_id??user?.id);
  if(!id||typeof user?.username!=='string'||!user.username.trim())return {...failed,reason:'missing_identity',message:'The response lacks a current-account ID and username.'};
  if(expectedId&&id!==expectedId)return {...failed,reason:'account_mismatch',message:'Instagram returned a different account from the expected session identity. Authentication is not verified.'};
  return {...base,verified:true,upstreamStatus:r.status,account:{id,username:user.username},identityMatch:expectedId?'matched':'not_requested',message:`Authenticated as @${user.username}. Instagram returned this session’s current-account identity.${expectedId?' The account ID matches the expected identity.':''}`};
 }catch{return {...base,reason:'verification_failed',message:'Could not complete the authentication check. No authentication claim was made.'};}
}
