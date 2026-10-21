#!/usr/bin/env python3
"""Explicitly download the pinned optional JADX engine and verify it before use."""
import argparse,hashlib,os,tempfile,urllib.request
from pathlib import Path
URL='https://github.com/1013503897/jadx-headless-mcp/releases/download/v0.7.1/jadx-headless-mcp-0.7.1-all.jar'
SHA='6e5eacf500b64292bfb73c49797c1958f6ee44646e43e868039ae7feb573ff75'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'tools/jadx-headless-mcp-0.7.1-all.jar');a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
 if a.output.exists():
  if hashlib.sha256(a.output.read_bytes()).hexdigest()!=SHA:p.error('Existing file has a different digest; choose another output path. It was not overwritten.')
 else:
  fd,name=tempfile.mkstemp(dir=a.output.parent,suffix='.part');os.close(fd);temporary=Path(name)
  try:
   with urllib.request.urlopen(URL,timeout=120) as response,temporary.open('wb') as out:
    while chunk:=response.read(1024*1024):out.write(chunk)
   if hashlib.sha256(temporary.read_bytes()).hexdigest()!=SHA:raise SystemExit('Downloaded JAR digest did not match; file rejected.')
   temporary.replace(a.output)
  finally:temporary.unlink(missing_ok=True)
 print('Verified JADX 0.7.1. Set REA_JADX_MCP_JAR to: '+str(a.output.resolve()))
if __name__=='__main__':main()
