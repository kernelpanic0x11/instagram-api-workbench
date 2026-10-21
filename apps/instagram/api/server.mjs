import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {createProxy} from './proxy.mjs';
const root=import.meta.dirname, port=Number(process.env.PORT||8766);
const origin=`http://127.0.0.1:${port}`;
const proxy=createProxy({origin});
http.createServer(async(req,res)=>{
 if(req.headers.host!==new URL(origin).host){res.writeHead(403).end('Invalid local host');return;}
 if(await proxy(req,res))return;
 let p;try{p=decodeURIComponent(new URL(req.url,'http://localhost').pathname)}catch{res.writeHead(400).end();return}
 const file=path.resolve(root,'.'+(p==='/'?'/index.html':p));
 if(!file.startsWith(root+path.sep)||p.includes('/node_modules/')){res.writeHead(403).end();return;}
 fs.stat(file,(err,s)=>{if(err||!s.isFile()){res.writeHead(404).end('Not found');return;}
 res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.yaml':'application/yaml','.txt':'text/plain'})[path.extname(file)]||'application/octet-stream');
 res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Cache-Control','no-cache');fs.createReadStream(file).pipe(res);});
}).listen(port,'127.0.0.1',()=>console.log(`Instagram API catalog: http://127.0.0.1:${port}`));
