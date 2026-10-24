#!/usr/bin/env python3
"""Link known requests to JSON parsers and recover root-reader dispatch keys.

Uses control-flow joins rather than nearby strings. All schemas remain partial:
recognized keys do not establish wire types, server requiredness or status codes.
"""
import argparse
from collections import deque
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path
from extract import Dex, DEFAULT_PROFILE, RESPONSE_FACTORIES, HELPERS, load_profile, scan, sig

DIRECTORY = Path(__file__).resolve().parent
FIELD_READER = ('LX/01yt;', 'A08', '(LX/04s3;)Ljava/lang/String;')
STRING_EQUALS = ('Ljava/lang/String;', 'equals', '(Ljava/lang/Object;)Z')
COMMON_DISPATCH = ('LX/01pP;', 'A01', '(LX/04s3;LX/01y9;Ljava/lang/String;)V')
# Independently reviewed nullable wrappers in the pinned APK. Each checks for
# VALUE_NULL, otherwise delegates the untouched reader to this static parser.
NULLABLE_PARSER_HELPERS = {
    ('LX/0D79;', 'A0H', '(LX/04s3;)Lcom/instagram/api/schemas/PageInfoImpl;'): 'LX/0ZTO;',
    ('LX/0D79;', 'A0I', '(LX/04s3;)LX/0IP4;'): 'LX/0L5F;',
    ('LX/0D79;', 'A0K', '(LX/04s3;)Lcom/instagram/model/reels/ReelResponseItem;'): 'LX/03kV;',
}



def invoke_arguments(dex, instruction):
    _, word, opcode, _, offset = instruction
    if opcode in range(0x6e, 0x73):
        count, tail = word >> 12, dex.u16(offset + 4)
        return [(tail >> (4 * index)) & 15 for index in range(min(count, 4))] + ([(word >> 8) & 15] if count == 5 else [])
    return list(range(dex.u16(offset + 4), dex.u16(offset + 4) + (word >> 8)))


def successors(dex, instruction, valid):
    pc, word, opcode, width, offset = instruction
    following = pc + width
    if opcode in (0x0e, 0x0f, 0x10, 0x11, 0x27) or opcode == 0 and word:
        return []
    if opcode in (0x28, 0x29, 0x2a):
        delta = struct.unpack_from('<b', dex.d, offset + 1)[0] if opcode == 0x28 else struct.unpack_from('<h' if opcode == 0x29 else '<i', dex.d, offset + 2)[0]
        candidates = [pc + delta]
    elif opcode in range(0x32, 0x3e):
        candidates = [following, pc + struct.unpack_from('<h', dex.d, offset + 2)[0]]
    elif opcode in (0x2b, 0x2c):
        payload = offset + dex.i32(offset + 2) * 2
        count = dex.u16(payload + 2)
        targets = payload + 8 if opcode == 0x2b else payload + 4 + count * 4
        candidates = [following] + [pc + dex.i32(targets + index * 4) for index in range(count)]
    else:
        candidates = [following]
    return [candidate for candidate in candidates if candidate in valid]


def transfer(dex, instruction, before):
    """Retain only immutable literals, the input reader, and its decoded key."""
    pc, word, opcode, _, offset = instruction
    state = dict(before)
    pending = state.pop(-1, None)
    high = word >> 8
    if opcode in (0x01, 0x04, 0x07):
        destination, value = high & 15, state.get(high >> 4)
    elif opcode in (0x02, 0x05, 0x08):
        destination, value = high, state.get(dex.u16(offset + 2))
    elif opcode in (0x03, 0x06, 0x09):
        destination, value = dex.u16(offset + 2), state.get(dex.u16(offset + 4))
    elif opcode in (0x0a, 0x0b, 0x0c):
        destination, value = high, pending
    elif opcode in (0x1a, 0x1b):
        index = dex.u16(offset + 2) if opcode == 0x1a else dex.u32(offset + 2)
        destination, value = high, ('literal', dex.strings[index], pc, index)
    elif opcode == 0x62:
        field = dex.fields[dex.u16(offset + 2)]
        destination, value = high, ('parser_instance', field[2], pc)
    elif opcode in range(0x6e, 0x73) or opcode in range(0x74, 0x79):
        method = dex.methods[dex.u16(offset + 2)]
        arguments = invoke_arguments(dex, instruction)
        if method == FIELD_READER and len(arguments) == 1 and state.get(arguments[0]) == ('reader',):
            state[-1] = ('field_key', pc)
        return state
    elif opcode == 0x1f:
        return state
    elif opcode == 0x12:
        destination, value = high & 15, None
    elif opcode in range(0x13, 0x1a) or opcode in (0x1c, 0x20, 0x21, 0x23) or opcode in range(0x2d, 0x32) or opcode in range(0x44, 0x4b) or opcode in range(0x52, 0x59) or opcode in range(0x60, 0x67) or opcode in range(0x7b, 0xe3) or opcode in (0xfe, 0xff):
        destination = high & 15 if opcode in (0x20, 0x21, 0x23) or opcode in range(0x52, 0x59) or opcode in range(0x7b, 0x90) or opcode in range(0xb0, 0xd8) else high
        value = None
        state.pop(destination + 1, None)
    else:
        return state
    state.pop(destination, None)
    if value is not None:
        state[destination] = value
    if opcode in (0x04, 0x05, 0x06, 0x0b):
        state.pop(destination + 1, None)
    return state


def matched_reader_call(dex, comparison, incoming, instructions, predecessors):
    """Follow only the equality-true exclusive prefix, stopping at joins/branches.

    A reader call is client evidence, not proof of JSON wire types or requiredness.
    Shared cleanup, nested control flow and exception-handler paths are excluded.
    """
    pc, _, _, width, _ = comparison
    result = instructions.get(pc + width)
    if not result or result[2] != 0x0a:  # move-result Boolean from String.equals
        return None
    register = result[1] >> 8
    branch = instructions.get(result[0] + result[3])
    if not branch or branch[2] not in (0x38, 0x39) or branch[1] >> 8 != register:
        return None
    following = branch[0] + branch[3]
    target = branch[0] + struct.unpack_from('<h', dex.d, branch[4] + 2)[0]
    if target == following:
        return None
    current, previous = (following if branch[2] == 0x38 else target), branch[0]
    for _ in range(24):
        instruction = instructions.get(current)
        if not instruction or predecessors.get(current) != {previous}:
            return None
        _, _, opcode, width, offset = instruction
        if opcode in range(0x28, 0x3e) or opcode in (0x0e, 0x0f, 0x10, 0x11, 0x27):
            return None
        if opcode in (*range(0x6e, 0x73), *range(0x74, 0x79)):
            method = dex.methods[dex.u16(offset + 2)]
            args = invoke_arguments(dex, instruction)
            reader_args = [index for index, register in enumerate(args) if incoming.get(current, {}).get(register) == ('reader',)]
            if reader_args:
                descriptor = method[2].split(')', 1)[1]
                if method in (FIELD_READER, COMMON_DISPATCH) or descriptor == 'V':
                    return None
                if descriptor == 'LX/01yl;' and method != ('LX/04s3;', 'A1d', '()LX/01yl;'):
                    return None  # A token advance/unknown token effect changes value context.
                if descriptor != 'LX/01yl;':  # Reviewed current-token peek is not value evidence.
                    return {'callee': sig(method), 'return_descriptor': descriptor,
                            'reader_argument_indices': reader_args, 'code_unit_offset': current,
                            'dex_byte_offset': offset, 'scope': 'first-reader-call-on-exclusive-equality-true-prefix'}
        previous, current = current, current + width
    return None


def dispatch_keys(dex, method_index, code, delegated_key=False):
    instructions, _ = dex.insns(code)
    by_pc = {instruction[0]: instruction for instruction in instructions}
    readers = [instruction for instruction in instructions if instruction[2] in (*range(0x6e, 0x73), *range(0x74, 0x79)) and dex.methods[dex.u16(instruction[4] + 2)] == FIELD_READER]
    # Multiple key-reading sites may describe nested inline object parsers.
    if len(readers) != (0 if delegated_key else 1):
        return [], 'multiple_or_missing_field_reader_sites'
    entry = {dex.u16(code) - 1: ('reader',)}
    if delegated_key:
        if dex.methods[method_index] != COMMON_DISPATCH:
            raise ValueError('Only the independently traced common field dispatcher accepts delegated keys')
        entry = {dex.u16(code) - 3: ('reader',), dex.u16(code) - 1: ('field_key', -1)}
    incoming = {0: entry}
    queue = deque([0])
    while queue:
        pc = queue.popleft()
        state = transfer(dex, by_pc[pc], incoming[pc])
        for target in successors(dex, by_pc[pc], by_pc):
            merged = state if target not in incoming else {register: value for register, value in state.items() if incoming[target].get(register) == value}
            if target not in incoming or merged != incoming[target]:
                incoming[target] = dict(merged)
                queue.append(target)
    predecessors = {}
    for source, instruction in by_pc.items():
        for target in successors(dex, instruction, by_pc):
            predecessors.setdefault(target, set()).add(source)
    fields = {}
    field_calls = {}
    for pc, instruction in by_pc.items():
        if pc not in incoming or instruction[2] not in (*range(0x6e, 0x73), *range(0x74, 0x79)):
            continue
        if dex.methods[dex.u16(instruction[4] + 2)] != STRING_EQUALS:
            continue
        arguments = invoke_arguments(dex, instruction)
        if len(arguments) != 2:
            continue
        values = [incoming[pc].get(register) for register in arguments]
        key = next((value for value in values if value and value[0] == 'field_key'), None)
        literal = next((value for value in values if value and value[0] == 'literal'), None)
        if not key or not literal or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]{0,99}', literal[1]):
            continue
        evidence = {'dex': dex.name, 'caller': sig(dex.methods[method_index]), 'code_unit_offset': pc,
                    'dex_byte_offset': instruction[4], 'field_reader_code_unit_offset': key[1] if key[1] >= 0 else None,
                    'key_source': 'verified-delegated-key-parameter' if delegated_key else 'input-reader-key',
                    'literal_code_unit_offset': literal[2], 'string_index': literal[3],
                    'comparison': sig(STRING_EQUALS), 'field_reader': sig(FIELD_READER)}
        fields.setdefault(literal[1], []).append(evidence)
        call = matched_reader_call(dex, instruction, incoming, by_pc, predecessors)
        if call:
            call.update(dex=dex.name, caller=sig(dex.methods[method_index]), comparison_code_unit_offset=pc)
            field_calls.setdefault(literal[1], []).append(call)
    return [{'name': name, 'evidence': evidence, 'client_reader_calls': field_calls.get(name, [])} for name, evidence in sorted(fields.items())], None


def parser_delegates(dex, method_index, code):
    """Accept only an untouched input reader delegated before any branch."""
    state = {dex.u16(code) - 1: ('reader',)}
    delegates = []
    for instruction in dex.insns(code)[0]:
        pc, _, opcode, _, offset = instruction
        if opcode in range(0x28, 0x3e) or opcode in (0x0e, 0x0f, 0x10, 0x11, 0x27):
            break
        if opcode in (*range(0x6e, 0x73), *range(0x74, 0x79)):
            method = dex.methods[dex.u16(offset + 2)]
            arguments = invoke_arguments(dex, instruction)
            values = [state.get(register) for register in arguments]
            if method == ('LX/05Bj;', 'parseFromJsonParser', '(LX/04s3;)Ljava/lang/Object;') and len(values) == 2 and values[0] and values[0][0] == 'parser_instance' and values[1] == ('reader',):
                delegates.append({'type': values[0][1], 'evidence': {'dex': dex.name, 'caller': sig(dex.methods[method_index]),
                                  'dex_byte_offset': offset, 'code_unit_offset': pc, 'callee': sig(method)}})
                break
            if ('reader',) in values and not (method[0] == 'LX/05s2;' and method[1] in ('A0V', 'A0R', 'A0T')):
                break
        state = transfer(dex, instruction, state)
    return delegates


def collect(apk, observations):
    profile = load_profile(DEFAULT_PROFILE)
    with apk.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != profile['apk_sha256']:
        raise ValueError('APK differs from the validated profile')
    callers = {(item['dex'], item['caller']) for operation in observations['operations'] for item in operation['evidence']}
    pairs = {(operation['method'], operation['path']) for operation in observations['operations']}
    bindings, error_bindings = {}, {}
    nullable_helpers = {}
    with zipfile.ZipFile(apk) as archive:
        dex_names = [name for name in archive.namelist() if re.fullmatch(r'classes\d*\.dex', name)]
        for name in dex_names:
            dex = Dex(archive.read(name), name)
            for method_index, code in dex.codes():
                method = dex.methods[method_index]
                if method in NULLABLE_PARSER_HELPERS:
                    instructions, _ = dex.insns(code)
                    parser_type = NULLABLE_PARSER_HELPERS[method]
                    referenced_fields = [dex.fields[dex.u16(offset + 2)] for _, _, opcode, _, offset in instructions if opcode == 0x62]
                    if (parser_type, 'A00', parser_type) not in referenced_fields or ('LX/01yl;', 'A0G', 'LX/01yl;') not in referenced_fields:
                        raise ValueError('Reviewed nullable parser wrapper differs from its mapping')
                    nullable_helpers[sig(method)] = {'parser_type':parser_type, 'scope':'reviewed-null-guarded-client-parser-delegation',
                        'dex':name, 'method':sig(method), 'code_item_byte_offset':code,
                        'dex_sha256':hashlib.sha256(dex.d).hexdigest(),
                        'instruction_code_units':[[dex.u16(offset + index * 2) for index in range(width)] for _, _, _, width, offset in instructions]}
                if (name, sig(dex.methods[method_index])) not in callers:
                    continue
                for observation in scan(dex, method_index, code, include_request_fields=True):
                    key = observation['method'], observation['path']
                    parser = observation.get('response_parser')
                    error = observation.get('error_parser')
                    if key in pairs and error:
                        records = error_bindings.setdefault(key, [])
                        if error not in records:
                            records.append(error)
                    if key not in pairs or not parser:
                        continue
                    records = bindings.setdefault(key, [])
                    if parser not in records:
                        records.append(parser)
            print('bindings', name, flush=True)
        wanted = {parser['type'] for mapping in (bindings, error_bindings) for records in mapping.values() for parser in records}
        if set(nullable_helpers) != {sig(method) for method in NULLABLE_PARSER_HELPERS}:
            raise ValueError('Reviewed nullable parser wrappers missing from APK')
        wanted.update(item['parser_type'] for item in nullable_helpers.values())
        parsers, helper_evidence, factory_evidence = {}, [], []
        common_fields = None
        # Revisit DEX files when a purged/forwarding parser names another parser.
        # Three delegate hops are a bounded closure, never an exhaustive claim.
        for pass_index in range(4):
            before = set(wanted)
            for name in dex_names:
                data = archive.read(name)
                dex = Dex(data, name)
                for method_index, code in dex.codes():
                    method = dex.methods[method_index]
                    if pass_index == 0 and method == FIELD_READER:
                        instructions, _ = dex.insns(code)
                        helper_evidence.append({'dex': name, 'method': sig(method), 'dex_sha256': hashlib.sha256(data).hexdigest(),
                                                'code_item_byte_offset': code, 'instruction_code_units': [[dex.u16(offset + index * 2) for index in range(width)] for _, _, _, width, offset in instructions]})
                    if pass_index == 0 and (method in RESPONSE_FACTORIES or method in HELPERS or method[0] == 'LX/03az;' or method[0:2] == ('LX/04x5;', '<init>') or method == COMMON_DISPATCH or method[0:2] == ('LX/01pP;', 'unsafeParseFromJson')):
                        instructions, _ = dex.insns(code)
                        factory_evidence.append({'dex': name, 'method': sig(method), 'dex_sha256': hashlib.sha256(data).hexdigest(),
                                                 'code_item_byte_offset': code, 'instruction_code_units': [[dex.u16(offset + index * 2) for index in range(width)] for _, _, _, width, offset in instructions]})
                    if method == COMMON_DISPATCH:
                        common_fields, _ = dispatch_keys(dex, method_index, code, delegated_key=True)
                    if method[0] not in wanted or method[0] in parsers or method[1:] != ('unsafeParseFromJson', '(LX/04s3;)Ljava/lang/Object;'):
                        continue
                    fields, skipped = dispatch_keys(dex, method_index, code)
                    delegates = parser_delegates(dex, method_index, code)
                    wanted.update(delegate['type'] for delegate in delegates)
                    parsers[method[0]] = {'type': method[0], 'method': sig(method), 'dex': name,
                        'dex_sha256': hashlib.sha256(data).hexdigest(), 'code_item_byte_offset': code,
                        'recognized_fields': fields, 'skip_reason': skipped, 'delegates': delegates}
                print('parsers', pass_index, name, flush=True)
            if wanted == before:
                break
        if common_fields and 'LX/01pP;' in parsers:
            parsers['LX/01pP;']['recognized_fields'] = common_fields
            parsers['LX/01pP;']['delegated_field_dispatcher'] = sig(COMMON_DISPATCH)
        for _ in range(4):
            for parser in parsers.values():
                existing = {field['name'] for field in parser['recognized_fields']}
                for delegate in parser['delegates']:
                    for field in parsers.get(delegate['type'], {}).get('recognized_fields', []):
                        if field['name'] not in existing:
                            parser['recognized_fields'].append(field)
                            existing.add(field['name'])
                parser['recognized_fields'].sort(key=lambda field: field['name'])
    for parser in parsers.values():
        for field in parser['recognized_fields']:
            for call in field.get('client_reader_calls', []):
                if call['callee'] in nullable_helpers:
                    call['nested_parser'] = nullable_helpers[call['callee']]['parser_type']
                    call['null_guard'] = 'VALUE_NULL returns null without delegating; other tokens enter parser'
    operations = [{'method': method, 'path': path, 'parsers': records} for (method, path), records in sorted(bindings.items())]
    error_operations = [{'method': method, 'path': path, 'parsers': records} for (method, path), records in sorted(error_bindings.items())]
    return {'source_apk_sha256': digest, 'operations': operations, 'error_operations': error_operations, 'parsers': parsers, 'field_reader_evidence': helper_evidence, 'factory_evidence': factory_evidence, 'nullable_parser_helpers': nullable_helpers,
            'stats': {'operations_with_parser_binding': len(operations), 'parser_types': len(wanted),
                      'operations_with_error_parser_binding': len(error_operations),
                      'parsers_with_recognized_fields': sum(bool(parser['recognized_fields']) for parser in parsers.values()),
                      'recognized_field_names_by_parser': sum(len(parser['recognized_fields']) for parser in parsers.values()),
                      'fields_with_client_reader_calls': sum(bool(field.get('client_reader_calls')) for parser in parsers.values() for field in parser['recognized_fields'])},
            'limitations': ['Only verified request factories with a static parser argument are bound.',
                           'Only a single root-reader key-reading site and CFG-proven String.equals comparisons are accepted.',
                           'Recognized parser keys are partial. Wire value types, nullability, nested shapes, server requiredness, exhaustive status codes and server error variants remain unresolved.',
                           'Exception-handler paths and obfuscated/dynamic keys are not recovered. No account or server requests were used.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, default=DIRECTORY.parents[1] / 'apks/base.apk')
    parser.add_argument('--output', type=Path, default=DIRECTORY / 'response-contracts.json')
    arguments = parser.parse_args()
    result = collect(arguments.apk, json.loads((DIRECTORY / 'operations.json').read_text()))
    arguments.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['stats']))


if __name__ == '__main__':
    main()
