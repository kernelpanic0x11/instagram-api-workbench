#!/usr/bin/env python3
"""Recover selected Discord bytecode references using an external, pinned hermes-dec checkout."""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
from research_inputs import extract_member

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_TOOL_COMMIT = '2e796663e1fedb93dca51060797ebf3327b3fedb'
TARGETS = {'/users/@me', '/users/@me/settings', 'getAPIBaseURL', 'API_ENDPOINT'}


def trace(tool_directory):
    tool_commit = subprocess.check_output(['git', '-C', str(tool_directory), 'rev-parse', 'HEAD'], text=True).strip()
    if tool_commit != EXPECTED_TOOL_COMMIT:
        raise ValueError('Use the reviewed hermes-dec commit documented in docs/DEEP_ANALYSIS.md')
    sys.path.insert(0, str(tool_directory / 'src'))
    from hermes_dec.parsers.hbc_file_parser import HBCReader
    from hermes_dec.parsers.hbc_bytecode_parser import parse_hbc_bytecode
    bundle = extract_member('discord', 'base.apk', 'assets/index.android.bundle', 'bundle.hbc')
    data = bundle.read_bytes()
    references, errors = [], []
    with bundle.open('rb') as source:
        reader = HBCReader()
        reader.read_whole_file(source)
        target_ids = {index: value for index, value in enumerate(reader.strings) if value in TARGETS}
        encodings = {index: [struct.pack('<I', index)] + ([struct.pack('<H', index)] if index < 65536 else [])
                     for index in target_ids}
        candidate_count = 0
        for function_id, header in enumerate(reader.function_headers):
            bytecode = data[header.offset:header.offset + header.bytecodeSizeInBytes]
            if not any(pattern in bytecode for patterns in encodings.values() for pattern in patterns):
                continue
            candidate_count += 1
            try:
                instructions = list(parse_hbc_bytecode(header, reader))
                hits = []
                for position, instruction in enumerate(instructions):
                    for operand_index, operand in enumerate(instruction.inst.operands):
                        if operand.operand_meaning and operand.operand_meaning.name == 'string_id':
                            string_id = getattr(instruction, f'arg{operand_index + 1}')
                            if string_id in target_ids:
                                hits.append((position, string_id))
                if not hits:
                    continue
                # Selected excerpts preserve neighboring register operations, not whole function dumps.
                positions = set()
                for position, _ in hits:
                    positions.update(range(max(0, position - 8), min(len(instructions), position + 13)))
                if reader.strings[header.functionName] in ('getAPIBaseURL', 'prepareRequest'):
                    positions = set(range(len(instructions)))
                excerpts = []
                for position in sorted(positions):
                    instruction = instructions[position]
                    operands = []
                    for operand_index, operand in enumerate(instruction.inst.operands):
                        value = getattr(instruction, f'arg{operand_index + 1}')
                        meaning = operand.operand_meaning.name if operand.operand_meaning else operand.operand_type.name
                        item = {'kind': meaning, 'value': value}
                        if meaning == 'string_id':
                            string = reader.strings[value]
                            item['string'] = string if len(string) <= 300 else '[long string omitted]'
                        operands.append(item)
                    excerpts.append({'function_byte_offset': instruction.original_pos,
                                     'bundle_byte_offset': header.offset + instruction.original_pos,
                                     'opcode': instruction.inst.name, 'operands': operands})
                references.append({'function_id': function_id, 'function_name': reader.strings[header.functionName],
                                   'bundle_byte_offset': header.offset, 'bytecode_bytes': header.bytecodeSizeInBytes,
                                   'target_strings': sorted({target_ids[index] for _, index in hits}), 'instructions': excerpts})
            except (NotImplementedError, IndexError, ValueError, KeyError, struct.error) as error:
                errors.append({'function_id': function_id, 'error_type': type(error).__name__})
    result = {'app': 'discord', 'source_apk': 'base.apk', 'source_member': 'assets/index.android.bundle',
              'bundle_sha256': hashlib.sha256(data).hexdigest(), 'hermes_version': reader.header.version,
              'tool': {'repository': 'https://github.com/P1sec/hermes-dec',
                       'commit': tool_commit},
              'stats': {'functions': len(reader.function_headers), 'strings': len(reader.strings),
                        'prefiltered_functions': candidate_count, 'matched_functions': len(references), 'decode_errors': len(errors)},
              'references': references, 'errors': errors,
              'limitations': ['The external parser warns that Hermes v98 is not formally supported. Results are provisional.',
                              'Selected literal references and neighboring instructions; getAPIBaseURL and prepareRequest retain complete instruction listings. No complete call graph or dataflow analysis.',
                              'Byte prefilter hits are accepted only after instruction decoding confirms a string operand.',
                              'Property names and neighboring calls alone do not prove HTTP method, host binding, runtime execution or endpoint availability.',
                              'No API requests, login, account storage or runtime instrumentation.']}
    destination = ROOT / 'apps/discord/evidence/hermes-trace.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['stats']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-directory', type=Path, default=ROOT / 'tools/hermes-dec')
    trace(parser.parse_args().tool_directory.resolve())


if __name__ == '__main__':
    main()
