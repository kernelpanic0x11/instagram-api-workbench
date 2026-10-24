#!/usr/bin/env python3
"""Bind the frozen remaining-read review to pinned caller and key-decoder bytecode."""
import importlib.util
import json
import struct
import zipfile
from pathlib import Path
from extract import Dex, sig

DIRECTORY = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location('shared', DIRECTORY / 'trace-shared-contracts.py')
shared = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(shared)
KEY_CASES = {
    'LX/0021;': {0x140: 'media_infos'},
    'LX/0C4G;': {0x44f: 'compound_product_ids'},
    'LX/0000;': {0x5ff: 'page_type', 0x38e: 'should_disable_exposures'},
    'LX/0005;': {0x40: 'horizon_world_id'},
    'LX/0018;': {0x7f: 'user_fbid'},
    'LX/020R;': {0x44d: 'include_social_context'},
}
EXTRA_METHODS = {
    ('LX/0Hqg;', 'B4p', '(Ljava/lang/String;Ljava/lang/String;)LX/09AD;'),
    ('LX/0Dlh;', '<init>', '(Lcom/instagram/common/session/UserSession;)V'),
    ('LX/0BWF;', 'A05', '(LX/0BWF;)Ljava/lang/Object;'),
    ('LX/0ECb;', 'onCreate', '(Landroid/os/Bundle;)V'),
    ('LX/0ZwX;', 'A02', '()LX/00fh;'),
    ('LX/0JTl;', 'A00', '(LX/06Sv;)Ljava/lang/String;'),
    ('LX/0bkh;', '<clinit>', '()V'), ('LX/0bkh;', 'toString', '()Ljava/lang/String;'),
    ('LX/02l6;', '<clinit>', '()V'), ('LX/02l6;', 'toString', '()Ljava/lang/String;'),
    ('LX/0123;', 'A0s', '()Ljava/lang/String;'),
} | {
    ('LX/0241;', '<clinit>', '()V'), ('LX/0241;', 'A00', '()Ljava/lang/String;'),
    ('LX/0241;', 'A01', '(III)Ljava/lang/String;'),
    ('LX/0242;', '<clinit>', '()V'), ('LX/0242;', 'A01', '()Ljava/lang/String;'),
    ('LX/0242;', 'A05', '(III)Ljava/lang/String;'),
}


def selector(signature):
    owner, tail = signature.split('->', 1)
    name, descriptor = tail.split('(', 1)
    return owner, name, '(' + descriptor


def switch_case_proof(dex, code, expected):
    """Retain only a reviewed packed-switch edge and its literal return, not the string table."""
    instructions = {pc: (word, opcode, width, offset) for pc, word, opcode, width, offset in dex.insns(code)[0]}
    result = []
    for pc, (word, opcode, width, offset) in instructions.items():
        if opcode != 0x2b:
            continue
        payload_pc = pc + struct.unpack_from('<i', dex.d, offset + 2)[0]
        payload = code + 16 + 2 * payload_pc
        if dex.u16(payload) != 0x100:
            raise ValueError('Expected packed-switch payload')
        size = dex.u16(payload + 2)
        first = struct.unpack_from('<i', dex.d, payload + 4)[0]
        for index, value in expected.items():
            if not first <= index < first + size:
                continue
            entry_offset = payload + 8 + 4 * (index - first)
            target_pc = pc + struct.unpack_from('<i', dex.d, entry_offset)[0]
            literal_word, literal_opcode, literal_width, literal_offset = instructions[target_pc]
            if literal_opcode not in (0x1a, 0x1b):
                raise ValueError('Reviewed case must immediately load its literal')
            string_index = dex.u16(literal_offset + 2) if literal_opcode == 0x1a else dex.u32(literal_offset + 2)
            return_word, return_opcode, _, return_offset = instructions[target_pc + literal_width]
            if dex.strings[string_index] != value or return_opcode != 0x11 or return_word >> 8 != literal_word >> 8:
                raise ValueError('Reviewed literal return differs')
            result.append({'index': index, 'value': value, 'switch_code_unit_offset': pc,
                           'switch_code_units': [dex.u16(offset + 2*i) for i in range(width)],
                           'payload_byte_offset': payload, 'payload_header_code_units': [dex.u16(payload + 2*i) for i in range(4)],
                           'entry_byte_offset': entry_offset, 'entry_code_units': [dex.u16(entry_offset), dex.u16(entry_offset + 2)],
                           'target_code_unit_offset': target_pc,
                           'literal_code_units': [dex.u16(literal_offset + 2*i) for i in range(literal_width)],
                           'return_code_unit': dex.u16(return_offset)})
    if len(result) != len(expected):
        raise ValueError('Missing reviewed switch case')
    return result


def main():
    review = json.loads((DIRECTORY.parent / 'remaining-read-review.json').read_text())
    shared.SELECTORS |= EXTRA_METHODS | {selector(caller) for operation in review['operations'] for caller in operation['callers']}
    apk = DIRECTORY.parents[1] / 'apks/base.apk'
    result = shared.collect(apk)
    if result['source_apk_sha256'] != review['source_apk_sha256']:
        raise ValueError('Review provenance differs')
    result.pop('rules', None)
    missing = {caller for operation in review['operations'] for caller in operation['callers']} - result['methods'].keys()
    if missing:
        raise ValueError('Reviewed caller proof unavailable')
    result['reviewed_routes'] = [operation['path'] for operation in review['operations']]
    result['key_decoders'] = {}
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not name.startswith('classes') or not name.endswith('.dex'):
                continue
            dex = Dex(archive.read(name), name)
            for method_index, code in dex.codes():
                owner, method, descriptor = dex.methods[method_index]
                if owner not in KEY_CASES or method != 'A00' or descriptor != '(I)Ljava/lang/String;':
                    continue
                result['key_decoders'][sig(dex.methods[method_index])] = {
                    'dex': name, 'code_item_byte_offset': code,
                    'cases': switch_case_proof(dex, code, KEY_CASES[owner])}
    if len(result['key_decoders']) != len(KEY_CASES):
        raise ValueError('Decoder proof unavailable')
    (DIRECTORY / 'remaining-read-evidence.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'reviewedRoutes': len(result['reviewed_routes']), 'callerAndHelperMethods': len(result['methods']), 'decodedKeys': sum(len(p['cases']) for p in result['key_decoders'].values())}))


if __name__ == '__main__':
    main()
