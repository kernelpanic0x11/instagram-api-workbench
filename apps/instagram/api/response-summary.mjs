export function describeResponse({status,contentType='',upstream=false,text=''}){
 if(!upstream){if(status===401)return 'No credentials loaded in the local proxy. Connect locally again; a server restart clears them.';return `Local proxy returned HTTP ${status}. This is not an Instagram authentication result.`;}
 const html=/text\/html/i.test(contentType)||/^\s*<!doctype html|^\s*<html/i.test(text);
 if(status===404)return `Instagram returned ${html?'an HTML page':'a response'} with HTTP 404. The endpoint or request context was not accepted; session validity is unknown.`;
 if(html)return `Instagram returned HTML (HTTP ${status}), not an API JSON response. Session validity is unknown; check the selected host, path, headers, or login/challenge flow.`;
 if(status===401||status===403)return `Instagram rejected this request (HTTP ${status}). Check the session, required headers and endpoint permissions; this response alone does not identify the cause.`;
 if(status===429)return 'Instagram rate-limited this request (HTTP 429). Stop retrying and respect the upstream retry interval.';
 if(status>=200&&status<300)return `Instagram responded with HTTP ${status}. Inspect the response to confirm the expected account and data; HTTP success alone does not verify authentication.`;
 return `Instagram returned HTTP ${status}. Authentication has not been independently verified.`;
}
