#!/usr/bin/env python3
"""Recover literal parameter keys on the same receiver as known request routes.

This offline pass preserves branch/escape boundaries and records encoding only
at verified finalizers. It does not infer server-required fields, parameter values,
response contracts or server acceptance.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from extract import Dex, PARAMETER_SETTERS, load_profile, scan, sig, DEFAULT_PROFILE

DIRECTORY = Path(__file__).resolve().parent


def collect(apk, operations):
    profile = load_profile(DEFAULT_PROFILE)
    with apk.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != profile['apk_sha256']:
        raise ValueError('APK differs from the validated mapping profile')
    if operations.get('source_apk_sha256', digest) != digest:
        raise ValueError('Route observations differ from the supplied APK')
    callers = {(evidence['dex'], evidence['caller']) for operation in operations['operations'] for evidence in operation['evidence']}
    known_pairs = {(operation['method'], operation['path']) for operation in operations['operations']}
    recovered, setter_evidence, dex_sources, transports = {}, [], [], {}
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            data = archive.read(name)
            dex = Dex(data, name)
            used = False
            for method_index, code in dex.codes():
                method = dex.methods[method_index]
                if method[0] == 'LX/04x6;' and method[1] in PARAMETER_SETTERS and method[2] == PARAMETER_SETTERS[method[1]][0]:
                    instructions, _ = dex.insns(code)
                    setter_evidence.append({'dex': name, 'method': sig(method), 'code_item_byte_offset': code,
                                            'instruction_code_units': [[dex.u16(offset + index * 2) for index in range(width)]
                                                                       for _, _, _, width, offset in instructions]})
                    used = True
                if (name, sig(method)) not in callers:
                    continue
                used = True
                for observation in scan(dex, method_index, code, include_request_fields=True):
                    key = observation['method'], observation['path']
                    if key not in known_pairs:
                        continue
                    if observation.get('request_transport'):
                        transport = observation['request_transport']
                        variants = transports.setdefault(key, [])
                        if transport not in variants:
                            variants.append(transport)
                    fields = recovered.setdefault(key, {})
                    for field in observation['request_fields']:
                        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]{0,99}', field['name']):
                            continue
                        result = fields.setdefault(field['name'], {'name': field['name'], 'wire_type': 'string',
                            'logical_types': [], 'required_status': 'unknown', 'client_presence_rules': [], 'client_serializations': [], 'evidence': []})
                        if field['logical_type'] not in result['logical_types']:
                            result['logical_types'].append(field['logical_type'])
                        if field['evidence'] not in result['evidence']:
                            result['evidence'].append(field['evidence'])
                        if field['client_presence'] not in result['client_presence_rules']:
                            result['client_presence_rules'].append(field['client_presence'])
                        if field['client_serialization'] not in result['client_serializations']:
                            result['client_serializations'].append(field['client_serialization'])
            if used:
                dex_sources.append({'dex': name, 'sha256': hashlib.sha256(data).hexdigest()})
            print(name, flush=True)
    results = [{'method': method, 'path': path, 'fields': sorted(fields.values(), key=lambda value: value['name'])}
               for (method, path), fields in sorted(recovered.items()) if fields]
    return {'source_apk_sha256': digest, 'profile': profile['name'], 'dex_sources': dex_sources,
            'setter_evidence': setter_evidence, 'operations': results,
            'transports': [{'method': method, 'path': path, 'variants': variants} for (method, path), variants in sorted(transports.items())],
            'stats': {'operations_with_fields': len(results), 'field_names_by_operation': sum(len(item['fields']) for item in results), 'operations_with_finalized_transport': len(transports)},
            'limitations': ['Only known method/route callers and literal keys on a shared receiver within one basic block.',
                           'Unknown calls, branches, receiver escapes and dynamic keys limit recovery. Missing fields are not evidence of a parameterless endpoint.',
                           'Setters populate a string parameter collection. Encoding is recorded only at verified finalizers; server requiredness and response schemas remain unresolved.',
                           'Values are deliberately omitted. No account credentials or runtime requests are used.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, default=DIRECTORY.parents[1] / 'apks/base.apk')
    parser.add_argument('--output', type=Path, default=DIRECTORY / 'request-fields.json')
    arguments = parser.parse_args()
    result = collect(arguments.apk, json.loads((DIRECTORY / 'operations.json').read_text()))
    arguments.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['stats']))


if __name__ == '__main__':
    main()
