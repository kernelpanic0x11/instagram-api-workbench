#!/usr/bin/env python3
"""Retain exported native networking bridge symbols and selected ARM64 excerpts."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from research_inputs import ROOT, extract_member

TARGETS = {
    'snapchat': ('libclient.so', r'Java_com_snapchat_client_grpc_UnifiedGrpcService.*(?:unaryCall|StreamingCall|create)$'),
    'tiktok': ('libsscronet.so', r'^Cronet_UrlRequest(?:Params_http_method_(?:get|set)|_InitWithParams|_Start)$'),
}


def trace(app, llvm_bin):
    name, pattern = TARGETS[app]
    library = extract_member(app, 'split_config.arm64_v8a.apk', 'lib/arm64-v8a/' + name, name)
    nm = llvm_bin / 'llvm-nm'
    objdump = llvm_bin / 'llvm-objdump'
    symbols = subprocess.check_output([str(nm), '--dynamic', '--defined-only', '--print-size', str(library)], text=True)
    matches = []
    for line in symbols.splitlines():
        fields = line.split()
        if len(fields) != 4 or not re.search(pattern, fields[3]):
            continue
        address, size = int(fields[0], 16), int(fields[1], 16)
        disassembly = subprocess.check_output([str(objdump), '-d', '--no-show-raw-insn',
                                               f'--start-address={address}', f'--stop-address={address + min(size, 128)}', str(library)], text=True)
        matches.append({'symbol': fields[3], 'virtual_address': address, 'symbol_size': size,
                        'assembly': [line.strip() for line in disassembly.splitlines() if re.match(r'^\s*[0-9a-f]+:', line)]})
    result = {'app': app, 'source_apk': 'split_config.arm64_v8a.apk', 'source_member': 'lib/arm64-v8a/' + name,
              'library_sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
              'tool': subprocess.check_output([str(objdump), '--version'], text=True).splitlines()[0],
              'symbols': matches,
              'limitations': ['Symbol names establish exported native entry points; only the first 128 bytes of each selected symbol are retained.',
                              'Exports alone do not bind an app endpoint, prove runtime use, establish payload fields or establish native protocol behavior.',
                              'No native call graph, runtime instrumentation, API requests or account storage access.']}
    (ROOT / 'apps' / app / 'evidence/native-bridges.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'app': app, 'symbols_retained': len(matches)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--llvm-bin', type=Path, default=Path('/opt/homebrew/opt/llvm/bin'))
    arguments = parser.parse_args()
    for app in TARGETS:
        trace(app, arguments.llvm_bin)


if __name__ == '__main__':
    main()
