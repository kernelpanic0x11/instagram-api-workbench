"""Resolve only pinned integer-switch helpers whose selected case returns a literal.

No APK code executes. Unknown indices, computed returns, overwritten registers,
nonstatic inputs and unreviewed method signatures remain unresolved.
"""
import hashlib
import re
import struct
import zipfile
from extract import Dex, sig

REVIEWED_KEY_DECODERS = {
    (owner, 'A00', '(I)Ljava/lang/String;')
    for owner in ('LX/0000;', 'LX/0005;', 'LX/0018;', 'LX/0021;', 'LX/0122;', 'LX/020R;', 'LX/0C4G;')
}


def literal_switch_cases(dex, method_index, code):
    instructions = dex.insns(code)[0]
    if not instructions:
        return {}
    pc, word, opcode, width, offset = instructions[0]
    # A static one-int input occupies the last register. No work precedes dispatch.
    if pc != 0 or opcode != 0x2b or dex.u16(code + 2) != 1 or word >> 8 != dex.u16(code) - 1:
        return {}
    payload_pc = pc + struct.unpack_from('<i', dex.d, offset + 2)[0]
    payload = code + 16 + 2 * payload_pc
    if dex.u16(payload) != 0x100:
        return {}
    count = dex.u16(payload + 2)
    first = struct.unpack_from('<i', dex.d, payload + 4)[0]
    by_pc = {instruction[0]: instruction for instruction in instructions}
    cases = {}
    for index in range(first, first + count):
        entry_offset = payload + 8 + 4 * (index - first)
        target = pc + struct.unpack_from('<i', dex.d, entry_offset)[0]
        literal = by_pc.get(target)
        if not literal or literal[2] not in (0x1a, 0x1b):
            continue
        _, literal_word, literal_opcode, literal_width, literal_offset = literal
        returned = by_pc.get(target + literal_width)
        if not returned or returned[2] != 0x11 or returned[1] >> 8 != literal_word >> 8:
            continue
        string_index = dex.u16(literal_offset + 2) if literal_opcode == 0x1a else dex.u32(literal_offset + 2)
        cases[index] = {'value': dex.strings[string_index], 'proof': {
            'dex': dex.name, 'method': sig(dex.methods[method_index]), 'method_index': method_index,
            'code_item_byte_offset': code, 'input_index': index,
            'switch_code_units': [dex.u16(offset + 2*i) for i in range(width)],
            'payload_byte_offset': payload, 'payload_header_code_units': [dex.u16(payload + 2*i) for i in range(4)],
            'entry_byte_offset': entry_offset, 'entry_code_units': [dex.u16(entry_offset), dex.u16(entry_offset + 2)],
            'target_code_unit_offset': target, 'literal_byte_offset': literal_offset,
            'literal_code_units': [dex.u16(literal_offset + 2*i) for i in range(literal_width)],
            'string_index': string_index, 'return_code_unit': returned[1]}}
    return cases


def load_literal_decoders(apk, expected_sha256):
    with apk.open('rb') as source:
        if hashlib.file_digest(source, 'sha256').hexdigest() != expected_sha256:
            raise ValueError('Literal-key decoder APK provenance differs')
    decoders = {}
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            data = archive.read(name)
            dex = Dex(data, name)
            if not any(method in REVIEWED_KEY_DECODERS for method in dex.methods):
                continue
            for method_index, code in dex.codes():
                method = dex.methods[method_index]
                if method not in REVIEWED_KEY_DECODERS:
                    continue
                cases = literal_switch_cases(dex, method_index, code)
                for case in cases.values():
                    case['proof']['dex_sha256'] = hashlib.sha256(data).hexdigest()
                decoders[method] = cases
    if set(decoders) != REVIEWED_KEY_DECODERS:
        raise ValueError('Reviewed literal-key decoder methods are missing')
    return decoders
