#!/usr/bin/env python3
"""Extract pinned Instagram login instructions offline; never read account storage."""
import argparse
import hashlib
import importlib.util
import json
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APK_SHA256 = '4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b'
SELECTED_METHODS = {
    'LX/0537;': {'A06'}, 'LX/0227;': {'A0c'}, 'LX/0224;': {'A1P'},
    'LX/0228;': {'A1K'}, 'LX/0221;': {'A1L', 'A0T'},
    'LX/0242;': {'A02', 'A04', 'A05', '<clinit>'},
    'LX/0hHh;': {'A00', '<init>', '<clinit>'}, 'LX/0hH7;': {'A00', '<clinit>'},
    'LX/0Gie;': {'A00', 'A01', 'A02'}, 'LX/0gTz;': {'<init>'},
    'LX/0g5z;': {'A00'}, 'LX/0KUd;': {'A00'},
    'Lcom/facebook/cryptopub/CryptoPubNative;': {'encrypt', '<clinit>'},
}
TARGET_LITERALS = {
    'accounts/two_factor_login/', 'accounts/send_two_factor_login_sms/',
    'ig-set-password-encryption-key-id', 'ig-set-password-encryption-pub-key',
    'ig-set-authorization', 'two_factor_identifier', 'accounts/fetch_headers/',
    'qe/sync/',
}


def load_instruction_helpers():
    spec = importlib.util.spec_from_file_location('login_dex_helpers', ROOT / 'scripts/trace-dex-candidates.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def trace(apk):
    with apk.open('rb') as source:
        checksum = hashlib.file_digest(source, 'sha256').hexdigest()
    if checksum != APK_SHA256:
        raise ValueError('APK differs from the pinned login research input')
    helpers = load_instruction_helpers()
    methods, sources = [], []
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            data = archive.read(name)
            dex = helpers.instruction_reader.Dex(data, name)
            literals = {index: value for index, value in enumerate(dex.strings) if value.lower() in TARGET_LITERALS}
            patterns = [re.compile(b'\x1a.' + re.escape(struct.pack('<H', index)), re.DOTALL)
                        for index in literals if index < 65536]
            patterns += [re.compile(b'\x1b.' + re.escape(struct.pack('<I', index)), re.DOTALL) for index in literals]
            count_before = len(methods)
            for index, code in dex.codes():
                owner, method, _ = dex.methods[index]
                selected = method in SELECTED_METHODS.get(owner, set())
                raw = data[code + 16:code + 16 + dex.u32(code + 12) * 2]
                if not selected and not any(pattern.search(raw) for pattern in patterns):
                    continue
                instructions, _ = dex.insns(code)
                records = [helpers.instruction_record(dex, instruction) for instruction in instructions]
                hits = sorted({record['string'] for record in records if record.get('string', '').lower() in TARGET_LITERALS})
                if selected or hits:
                    methods.append({'dex': name, 'method': helpers.instruction_reader.sig(dex.methods[index]),
                                    'code_item_byte_offset': code, 'target_literals': hits, 'instructions': records})
            if len(methods) > count_before:
                sources.append({'dex': name, 'sha256': hashlib.sha256(data).hexdigest()})
            print(f'{name}: selected {len(methods) - count_before} methods', flush=True)
    return {'app': 'instagram', 'version': '451.0.0.53.80', 'apk_sha256': APK_SHA256,
            'status': 'static evidence; no login request or server acceptance verified',
            'dex_sources': sources, 'methods': methods}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, default=ROOT / 'apps/instagram/apks/base.apk')
    parser.add_argument('--output', type=Path, default=ROOT / 'apps/instagram/evidence/login-trace.json')
    arguments = parser.parse_args()
    result = trace(arguments.apk)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'methods': len(result['methods']), 'network_requests': 0}))


if __name__ == '__main__':
    main()
