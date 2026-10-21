// Optional MCP stdio client. New captures go into an ignored directory, never over reference evidence.
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {mkdirSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {parseArgs} from 'node:util';
const {values}=parseArgs({options:{'output-dir':{type:'string'}}});
const directory=path.resolve(values['output-dir']||path.join(import.meta.dirname,'../runs/rea-'+new Date().toISOString().replaceAll(':','-')));
mkdirSync(directory,{recursive:true});
const pending=new Map();let id=0;
const child=spawn('sh',['../rea-local','--mcp'],{cwd:import.meta.dirname,stdio:['pipe','pipe','pipe']});
const fail=error=>{for(const {reject,timer}of pending.values()){clearTimeout(timer);reject(error)}pending.clear()};
child.on('error',fail);child.on('exit',()=>fail(new Error('REA exited. Run scripts/doctor.py --android and check REA_JADX_MCP_JAR.')));
child.stdin.on('error',fail);child.stderr.on('data',data=>process.stderr.write(data));
createInterface({input:child.stdout}).on('line',line=>{try{const r=JSON.parse(line);if(pending.has(r.id)){const entry=pending.get(r.id);pending.delete(r.id);clearTimeout(entry.timer);r.error?entry.reject(new Error(r.error.message)):entry.resolve(r.result)}}catch(error){fail(error)}});
function rpc(method,params){return new Promise((resolve,reject)=>{const n=++id,timer=setTimeout(()=>{pending.delete(n);reject(new Error('REA RPC timeout'))},180000);pending.set(n,{resolve,reject,timer});child.stdin.write(JSON.stringify({jsonrpc:'2.0',id:n,method,params})+'\n')})}
try{
 await rpc('initialize',{protocolVersion:'2024-11-05',capabilities:{},clientInfo:{name:'local-instagram-investigation',version:'2.0'}});
 child.stdin.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'})+'\n');
 const list=await rpc('tools/list',{});writeFileSync(path.join(directory,'tool-schemas.json'),JSON.stringify(list,null,2),{flag:'wx'});
 console.log(JSON.stringify({ready:true,outputDirectory:directory,android_tools:list.tools.filter(t=>t.name.includes('android')).map(t=>t.name)}));
 const rl=createInterface({input:process.stdin});
 for await(const line of rl){
  try{const task=JSON.parse(line);if(task.quit)break;if(!/^[A-Za-z0-9_-]+$/.test(task.file))throw new Error('file must be a unique simple capture name');const result=await rpc('tools/call',{name:task.name,arguments:task.args});writeFileSync(path.join(directory,task.file+'.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log(JSON.stringify({saved:task.file,isError:!!result.isError,evidenceId:result.structuredContent?.evidence_id}));}catch(error){console.log(JSON.stringify({error:error.message}))}
 }
 rl.close();process.stdin.pause();
}catch(error){console.error(error.message);process.exitCode=1}
finally{child.stdin.end();child.kill()}
