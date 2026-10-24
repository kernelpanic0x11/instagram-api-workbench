#!/usr/bin/env python3
"""Publish pinned, reviewable evidence for shared encoding and message handling."""
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path
from extract import Dex, DEFAULT_PROFILE, FINALIZERS, OBJECT_STRING_HELPER, PARAMETER_SETTERS, load_profile, sig

DIRECTORY = Path(__file__).resolve().parent
SELECTORS = {
    ('LX/04x6;', '<init>', '(LX/05Dd;)V'), ('LX/04x6;', 'A02', '()LX/02uC;'),
    ('LX/04x5;', 'A0K', '()LX/02sG;'),
    ('LX/03ao;', 'A00', '(Z)LX/0Plr;'), ('LX/03ao;', 'A01', '(Ljava/lang/String;)Ljava/lang/String;'),
    ('LX/03ao;', 'A05', '(Ljava/lang/String;Ljava/lang/String;)V'),
    ('LX/03gP;', '<init>', '(Ljava/util/List;Z)V'),
    ('LX/02sL;', 'A00', '(Ljava/util/List;)Ljava/lang/String;'),
    ('LX/01k4;', 'A00', '(LX/03ao;Ljava/util/Map;Ljava/util/Set;)Ljava/lang/String;'),
    ('LX/01yl;', '<clinit>', '()V'),
    ('LX/01y9;', 'A01', '(LX/04s3;)V'),
    ('LX/01pP;', 'A01', '(LX/04s3;LX/01y9;Ljava/lang/String;)V'),
    ('LX/02sE;', '<init>', '(LX/04x5;LX/0opA;LX/03pn;LX/0Ddm;LX/0Ddm;LX/02sD;)V'),
    ('LX/02sE;', 'call', '()Ljava/lang/Object;'),
    ('LX/041Z;', 'A00', '(LX/01Jp;LX/05Dd;LX/0Ddm;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;'),
    ('LX/0Kbr;', 'unsafeParseFromJson', '(LX/04s3;)Ljava/lang/Object;'),
} | {OBJECT_STRING_HELPER} | set(FINALIZERS) | {('LX/04x6;', name, descriptor) for name, (descriptor, _) in PARAMETER_SETTERS.items()}


def arguments(dex, instruction):
    _, word, opcode, _, offset = instruction
    if opcode in range(0x6e, 0x73):
        count, tail = word >> 12, dex.u16(offset + 4)
        return [(tail >> (4 * index)) & 15 for index in range(min(count, 4))] + ([(word >> 8) & 15] if count == 5 else [])
    return list(range(dex.u16(offset + 4), dex.u16(offset + 4) + (word >> 8)))


def token_enum(dex, code):
    values, constructed, tokens = {}, {}, {}
    for instruction in dex.insns(code)[0]:
        pc, word, opcode, _, offset = instruction
        destination = word >> 8
        if opcode in (0x1a, 0x1b):
            index = dex.u16(offset + 2) if opcode == 0x1a else dex.u32(offset + 2)
            values[destination] = ('string', dex.strings[index])
        elif opcode == 0x22:
            values[destination] = ('object', pc)
        elif opcode in (0x70, 0x76):
            method = dex.methods[dex.u16(offset + 2)]
            registers = arguments(dex, instruction)
            if method == ('LX/01yl;', '<init>', '(IILjava/lang/String;Ljava/lang/String;)V') and len(registers) == 5:
                receiver, name = values.get(registers[0]), values.get(registers[3])
                if receiver and name and receiver[0] == 'object' and name[0] == 'string':
                    constructed[receiver] = name[1]
        elif opcode == 0x69:
            field = dex.fields[dex.u16(offset + 2)]
            name = constructed.get(values.get(destination))
            if field[0] == 'LX/01yl;' and name:
                tokens[field[1]] = {'name': name, 'dex_byte_offset': offset}
        elif opcode == 0x12:
            values.pop(destination & 15, None)
        elif opcode in range(0x13, 0x1a) or opcode in (0x0a, 0x0b, 0x0c, 0x62):
            values.pop(destination, None)
    return tokens


def proof(dex, method_index, code, digest):
    records = []
    for pc, _, opcode, width, offset in dex.insns(code)[0]:
        record = {'code_unit_offset': pc, 'dex_byte_offset': offset,
                  'code_units': [dex.u16(offset + index * 2) for index in range(width)]}
        if opcode in (0x1a, 0x1b):
            index = dex.u16(offset + 2) if opcode == 0x1a else dex.u32(offset + 2)
            record['string'] = dex.strings[index]
        elif opcode == 0x13:
            record['integer'] = struct.unpack_from('<h', dex.d, offset + 2)[0]
        elif opcode in (*range(0x6e, 0x73), *range(0x74, 0x79)):
            record['callee'] = sig(dex.methods[dex.u16(offset + 2)])
        elif opcode in range(0x52, 0x6e):
            record['field'] = sig(dex.fields[dex.u16(offset + 2)])
        records.append(record)
    return {'dex': dex.name, 'dex_sha256': digest, 'method': sig(dex.methods[method_index]),
            'code_item_byte_offset': code, 'instructions': records}


def collect(apk):
    with apk.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != load_profile(DEFAULT_PROFILE)['apk_sha256']:
        raise ValueError('APK differs from the pinned input')
    methods, tokens = {}, {}
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            data = archive.read(name)
            dex = Dex(data, name)
            for method_index, code in dex.codes():
                method = dex.methods[method_index]
                if method not in SELECTORS:
                    continue
                methods[sig(method)] = proof(dex, method_index, code, hashlib.sha256(data).hexdigest())
                if method == ('LX/01yl;', '<clinit>', '()V'):
                    tokens = token_enum(dex, code)
    if set(methods) != {sig(method) for method in SELECTORS}:
        raise ValueError('Shared contract evidence is incomplete')
    expected = {'A0D': 'START_OBJECT', 'A0C': 'START_ARRAY', 'A09': 'END_OBJECT', 'A08': 'END_ARRAY', 'A0G': 'VALUE_NULL'}
    if any(tokens.get(field, {}).get('name') != name for field, name in expected.items()):
        raise ValueError('JSON token mapping differs from reviewed semantics')
    finalizer = methods['LX/04x6;->A02()LX/02uC;']
    literals = {instruction['string'] for instruction in finalizer['instructions'] if 'string' in instruction}
    if not {'signed_body', 'SIGNATURE.%s'} <= literals:
        raise ValueError('Signing-envelope literals were not found')
    dispatch = methods['LX/02sE;->call()Ljava/lang/Object;']
    forbidden = methods['LX/041Z;->A00(LX/01Jp;LX/05Dd;LX/0Ddm;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;']
    if 400 not in {instruction.get('integer') for instruction in dispatch['instructions']} or 403 not in {instruction.get('integer') for instruction in forbidden['instructions']}:
        raise ValueError('Error dispatch thresholds were not found')
    return {'source_apk_sha256': digest, 'methods': methods, 'json_tokens': tokens,
        'rules': {
            'requiredness': {'server_requiredness': 'unknown', 'nullable_setters': 'Null string/boxed Boolean values are omitted. Primitive setters serialize a value when executed. Branch reachability is separate from setter behavior.'},
            'encoding': {'get': 'The shared finalizer serializes the active parameter collection into the URL query.',
                         'post': 'Non-streaming parameters use UTF-8 application/x-www-form-urlencoded; a streaming parameter selects the multipart path.',
                         'scope': 'Shared client path. Per-operation applicability requires a receiver trace through finalization.'},
            'signing': {'condition': 'LX/04x6;->A0U is true at finalization', 'field': 'signed_body',
                        'prefix': 'SIGNATURE.', 'payload': 'The parameter collection and separate value map pass through LX/01k4;->A00. An exclusion set can leave parameters outside the envelope.',
                        'cryptography': 'This observed branch prepends a literal placeholder; it does not calculate a cryptographic signature. Other integrity/authentication mechanisms are not ruled out.'},
            'session_context': {'_uuid': 'Injected by the shared finalizer for POST when the session supplies a user ID.',
                                '_uid': 'Injected under the same condition when the signing-envelope flag is enabled.',
                                'server_requiredness': 'unknown', 'values': 'Not captured; the manual proxy does not synthesize these parameters.'},
            'message': {'object': 'An errors array is read from the object. Items are decoded with a String-coercing reader; null decoded entries throw in this client path.',
                        'array': 'A top-level message array is skipped in the common response model.',
                        'other_tokens': 'Delegated to the String-coercing reader and stored as scalar message text.',
                        'server_requiredness': 'unknown', 'wire_types': 'Client handling observations, not a closed server schema.'},
            'system_messages': {'container': '_messages', 'consumed_token': 'START_ARRAY', 'item_parser': 'LX/0Kbr;',
                                'client_required_item_fields': ['key', 'time'], 'decoded_types': {'key': 'nonnull String', 'time': 'float'},
                                'null_items': 'skipped', 'server_requiredness': 'unknown',
                                'scope': 'Required by the item parser when an object is consumed, not required on every server response.'},
            'error_dispatch': {'condition': 'HTTP status >= 400 enters the configured error-parser path.',
                               'special_403': 'HTTP 403 uses the common LX/01pP parser and error handler, then throws a status-bearing exception even when parsing succeeds.',
                               'other_errors': 'Other statuses >=400 use the request factory error parser.',
                               'ordinary_dispatch': 'Statuses below 400 use the ordinary parser path; this is not proof of successful authentication or a 2xx response.',
                               'server_status_sets': 'unknown per operation'}},
        'limitations': ['Pinned client implementation, not an authoritative server specification.',
                       'Conditional rules do not prove every route reaches this finalizer with the same flags.',
                       'No runtime responses, account values, credentials or network requests are used.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, default=DIRECTORY.parents[1] / 'apks/base.apk')
    parser.add_argument('--output', type=Path, default=DIRECTORY / 'shared-contracts.json')
    arguments_ = parser.parse_args()
    result = collect(arguments_.apk)
    arguments_.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'reviewed_methods': len(result['methods']), 'json_tokens': len(result['json_tokens'])}))
