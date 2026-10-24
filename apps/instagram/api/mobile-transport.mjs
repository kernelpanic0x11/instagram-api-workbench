import {spawn} from 'node:child_process';
// Credentials/body travel only over the child's stdin, never argv, environment or disk.
export function createMobileFetch({python, worker = new URL('../scripts/mobile-http-transport.py',import.meta.url).pathname, spawnImpl = spawn}) {
  return async function mobileFetch(url, options = {}) {
    if (new URL(url).origin !== 'https://i.instagram.com') throw new Error('Unsupported mobile destination');
    const headers = Object.fromEntries(new Headers(options.headers).entries());
    const request = JSON.stringify({url:String(url),method:options.method ?? 'GET',headers,body:Buffer.from(options.body ?? '').toString('base64')});
    return await new Promise((resolve,reject) => {
      const child=spawnImpl(python,[worker],{stdio:['pipe','pipe','pipe']});
      let chunks=[],size=0,settled=false;
      function finish(error,response){if(settled)return;settled=true;clearTimeout(timer);options.signal?.removeEventListener('abort',abort);error?reject(error):resolve(response);}
      function abort(){child.kill();finish(new DOMException('Mobile transport timed out.','TimeoutError'));}
      const timer=setTimeout(abort,30000);
      options.signal?.addEventListener('abort',abort,{once:true});
      if(options.signal?.aborted){abort();return;}
      child.stderr.on('data',()=>{}); // Never forward worker/third-party diagnostics containing request context.
      child.stdout.on('data',chunk=>{size+=chunk.length;if(size>46*1024*1024){child.kill();finish(new Error('Mobile response exceeds size limit'));return;}chunks.push(chunk);});
      child.on('error',()=>finish(new Error('Could not start mobile transport')));
      child.stdin.on('error',()=>finish(new Error('Could not submit mobile request')));
      child.on('close',code=>{
        if(settled)return;
        try{
          const result=JSON.parse(Buffer.concat(chunks).toString());
          if(code!==0||result.error||!Number.isInteger(result.status))throw new Error();
          const body=Buffer.from(result.body,'base64');
          finish(null,new Response(body.length?body:null,{status:result.status,headers:result.headers}));
        }catch{finish(new Error('Mobile transport failed'));}
      });
      child.stdin.end(request);
    });
  };
}
