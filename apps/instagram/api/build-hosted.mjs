import fs from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const out=path.resolve(process.argv[2]||path.join(root,'hosted'));
fs.mkdirSync(out,{recursive:true});
const spec=JSON.parse(fs.readFileSync(path.join(root,'openapi.json')));
const verbs=['get','post','put','patch','delete','options','head','trace'];
const pathCount=Object.keys(spec.paths).length,operationCount=Object.values(spec.paths).reduce((n,item)=>n+verbs.filter(v=>item[v]).length,0),unknownCount=Object.values(spec.paths).filter(item=>!verbs.some(v=>item[v])).length;
spec.servers=[{url:'https://i.instagram.com',description:'Static Android route evidence. Use the local workbench for authenticated requests.'}];
spec.info.description=operationCount+' traced client HTTP operations; '+unknownCount+' unresolved-method paths. Static configuration is not proof of live API availability. Browse the evidence here; clone the GitHub repository and run the local workbench to authenticate and execute requests. No credentials are collected by this public page.';
fs.writeFileSync(path.join(out,'openapi.json'),JSON.stringify(spec,null,2)+'\n');
for(const name of ['live.css'])fs.copyFileSync(path.join(root,name),path.join(out,name));
fs.mkdirSync(path.join(out,'vendor'),{recursive:true});
for(const name of ['swagger-ui.css','swagger-ui-bundle.js','swagger-ui-standalone-preset.js','LICENSE','NOTICE','swagger-ui-bundle.js.LICENSE.txt'])if(fs.existsSync(path.join(root,'vendor',name)))fs.copyFileSync(path.join(root,'vendor',name),path.join(out,'vendor',name));
const live=fs.readFileSync(path.join(root,'live.mjs'),'utf8');
const unresolved=live.slice(live.indexOf('async function mountUnresolved()'),live.indexOf('window.onload=')).replaceAll('Open in manual editor','Run in local workbench');
const helper=live.slice(live.indexOf('function element('),live.indexOf('function mountTools('));
fs.writeFileSync(path.join(out,'hosted.mjs'),helper+unresolved+`
function mountHostedTools(){
 const panel=element('section',{id:'hosted-tools',class:'swagger-ui wrapper'});
 panel.innerHTML='<div class="live-manual"><h3>Browse the APIs · Run requests locally</h3><p><strong>${operationCount} traced operations · ${pathCount.toLocaleString('en-US')} paths · ${unknownCount} unresolved routes.</strong> These are client-code findings, not a set of confirmed working APIs.</p><p><a class="btn" href="guide.html">Read the guide</a> <a class="btn" href="https://github.com/kernelpanic0x11/instagram-api-workbench" target="_blank" rel="noopener noreferrer">Get the code on GitHub</a> <a class="btn" href="http://127.0.0.1:8766/" target="_blank" rel="noopener noreferrer">Open local workbench</a></p><p>Clone the repository, then run:</p><pre>git clone https://github.com/kernelpanic0x11/instagram-api-workbench.git&#10;cd instagram-api-workbench/apps/instagram/api&#10;node server.mjs</pre><p>For browser login, install Google Chrome and run <code>npm ci</code> in <code>api</code>. In the local workbench choose <strong>Open Instagram login → Verify authentication → GET my account settings</strong>.</p><p>This public page collects no session cookies or tokens. Authentication runs on your machine. The hosted catalog disables API execution.</p></div>';
 document.querySelector('.scheme-container')?.before(panel);
 window.useRoute=()=>{panel.scrollIntoView({behavior:'smooth'});};
}
window.onload=()=>{window.ui=SwaggerUIBundle({url:'openapi.json',dom_id:'#swagger-ui',deepLinking:true,presets:[SwaggerUIBundle.presets.apis,SwaggerUIStandalonePreset],plugins:[SwaggerUIBundle.plugins.DownloadUrl],layout:'StandaloneLayout',filter:true,docExpansion:'none',supportedSubmitMethods:[],tryItOutEnabled:false,validatorUrl:null,persistAuthorization:false,requestInterceptor:req=>{const u=new URL(req.url,location.href),specUrl=new URL('openapi.json',location.href);if(u.origin===specUrl.origin&&u.pathname===specUrl.pathname&&(req.method||'GET').toUpperCase()==='GET')return req;throw new Error('Run authenticated requests in the local workbench.');},onComplete:()=>{mountHostedTools();mountUnresolved();}})};
`);
let html=fs.readFileSync(path.join(root,'index.html'),'utf8').replace('src="live.mjs"','src="hosted.mjs"');
html=html.replace('<title>','<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; connect-src \'self\'; font-src \'self\' data:; object-src \'none\'; base-uri \'none\'; form-action \'none\'">\n<title>');
const version=createHash('sha256').update(fs.readFileSync(path.join(out,'hosted.mjs'))).digest('hex').slice(0,12);html=html.replace('src="hosted.mjs"','src="hosted.mjs?v='+version+'"');
fs.writeFileSync(path.join(out,'index.html'),html);
fs.writeFileSync(path.join(out,'swagger.html'),html);
console.log(JSON.stringify({out,paths:Object.keys(spec.paths).length,operations:spec['x-coverage'].documentedOperations,execution:'local only'}));
