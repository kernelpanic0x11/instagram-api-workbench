#!/usr/bin/env python3
"""Trace selected TikTok/Snapchat literals to DEX instructions and method annotations.

Retains source locations and nearby invokes; does not infer HTTP verbs from proximity.
"""
import argparse
import hashlib
import importlib.util
import json
import struct
import zipfile
from pathlib import Path
from research_inputs import verified_apk

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    'tiktok': {'/aweme/v1/aweme/detail/', '/aweme/v1/notice/count/', '/tiktok/comment/status/batch_get/v1'},
    'snapchat': {'/loq/register_v2', '/snapchat.cameos.minerva.MinervaService/GenerateCaption',
                 '/snapchat.cdp.cof.CircumstancesService/targetingQuery'},
}


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


annotation_reader = load_module('apk_annotations', 'scripts/analyze-apks.py')
# Reuse the existing instruction decoder only; Instagram request mappings are not applied.
instruction_reader = load_module('dex_instructions', 'apps/instagram/api/bulk-trace/extract.py')


def method_annotations(dex):
    count, offset = struct.unpack_from('<II', dex.data, 96)
    for index in range(count):
        directory = dex.u32(offset + index * 32 + 20)
        if not directory:
            continue
        field_count, method_count = struct.unpack_from('<II', dex.data, directory + 4)
        for entry in range(method_count):
            method_index, annotation_set = struct.unpack_from('<II', dex.data, directory + 16 + field_count * 8 + entry * 8)
            for annotation_index in range(dex.u32(annotation_set)):
                location = dex.u32(annotation_set + 4 + annotation_index * 4)
                annotation, _ = dex.annotation(location + 1)
                yield method_index, location, annotation


def instruction_record(dex, instruction):
    pc, opcode, low_opcode, width, offset = instruction
    record = {'code_unit_offset': pc, 'dex_byte_offset': offset, 'opcode': hex(low_opcode),
              'code_units': [dex.u16(offset + index * 2) for index in range(width)]}
    if low_opcode in (0x1a, 0x1b):
        index = dex.u16(offset + 2) if low_opcode == 0x1a else dex.u32(offset + 2)
        value = dex.strings[index]
        record.update({'string_index': index, 'string': value if len(value) <= 300 else '[long string omitted]'})
    elif low_opcode in list(range(0x6e, 0x73)) + list(range(0x74, 0x79)):
        index = dex.u16(offset + 2)
        record['callee'] = instruction_reader.sig(dex.methods[index])
    elif low_opcode in (0x1c, 0x1f, 0x20, 0x22, 0x23):
        record['referenced_type'] = dex.types[dex.u16(offset + 2)]
    elif 0x52 <= low_opcode <= 0x6d:
        record['field'] = list(dex.fields[dex.u16(offset + 2)])
    return record


def trace(app):
    references, annotations, errors, dex_sources = [], [], [], []
    decoded_methods = 0
    for apk in sorted((ROOT / 'apps' / app / 'apks').glob('*.apk')):
        verified_apk(app, apk.name)
        with zipfile.ZipFile(apk) as archive:
            for name in archive.namelist():
                if not annotation_reader.DEX_MEMBER.fullmatch(name):
                    continue
                data = archive.read(name)
                dex_sources.append({'apk': apk.name, 'dex': name, 'sha256': hashlib.sha256(data).hexdigest()})
                dex = instruction_reader.Dex(data, name)
                wanted = {index: value for index, value in enumerate(dex.strings) if value in TARGETS[app]}
                if not wanted:
                    continue
                annotation_dex = annotation_reader.DexAnnotations(data)
                for method_index, location, annotation in method_annotations(annotation_dex):
                    values = annotation['elements']
                    matched = sorted({value for value in values.values() if isinstance(value, str) and value in TARGETS[app]})
                    if matched:
                        annotations.append({'apk': apk.name, 'dex': name, 'annotation_byte_offset': location,
                                            'declaring_method': annotation_dex.methods[method_index],
                                            'annotation_type': annotation['type'], 'elements': values,
                                            'target_strings': matched, 'http_method': None})
                for method_index, code_offset in dex.codes():
                    try:
                        instructions, _ = dex.insns(code_offset)
                        decoded_methods += 1
                        hits = []
                        for position, instruction in enumerate(instructions):
                            _, _, opcode, _, offset = instruction
                            if opcode in (0x1a, 0x1b):
                                index = dex.u16(offset + 2) if opcode == 0x1a else dex.u32(offset + 2)
                                if index in wanted:
                                    hits.append((position, index))
                        if not hits:
                            continue
                        positions = set()
                        for position, _ in hits:
                            positions.update(range(max(0, position - 6), min(len(instructions), position + 18)))
                        references.append({'apk': apk.name, 'dex': name,
                                           'declaring_method': instruction_reader.sig(dex.methods[method_index]),
                                           'target_strings': sorted({wanted[index] for _, index in hits}),
                                           'instructions': [instruction_record(dex, instructions[p]) for p in sorted(positions)]})
                    except (IndexError, KeyError, ValueError, struct.error) as error:
                        errors.append({'apk': apk.name, 'dex': name, 'method_index': method_index,
                                       'error_type': type(error).__name__})
        print(f'{app}: traced {apk.name}', flush=True)
    result = {'app': app, 'targets': sorted(TARGETS[app]), 'dex_sources': dex_sources,
              'stats': {'decoded_methods_in_target_dex_files': decoded_methods, 'referencing_methods': len(references),
                        'matching_method_annotations': len(annotations), 'decode_errors': len(errors)},
              'method_annotations': annotations, 'instruction_references': references, 'errors': errors,
              'limitations': ['Selected literals only, across all installed APKs. Instruction decoding is limited to DEX files containing those literals.',
                              'Neighboring instructions and invokes establish code locations, not same-object dataflow, method/path pairing, or runtime execution.',
                              'Obfuscated annotation types remain unnamed until their semantics are independently traced. No Instagram mappings reused.',
                              'Raw instruction units are retained for checking disassembly; native code and dynamic URL composition remain unresolved.',
                              'No API requests or account data accessed.']}
    (ROOT / 'apps' / app / 'evidence/dex-trace.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'app': app, **result['stats']}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apps', nargs='+', choices=list(TARGETS))
    for app in parser.parse_args().apps:
        trace(app)


if __name__ == '__main__':
    main()
