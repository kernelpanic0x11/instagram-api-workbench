#!/usr/bin/env python3
"""Inventory local APK sets and recover literal URLs and Retrofit method annotations.

Static only: does not launch apps, read account storage, or make API requests.
"""
import argparse
import collections
import hashlib
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HTTP_ANNOTATIONS = {f'L{namespace}/http/{verb};': verb
                    for namespace in ('retrofit2', 'retrofit', 'com/bytedance/retrofit2')
                    for verb in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'HTTP')}
ROUTE_LITERAL = re.compile(r'^/(?:[A-Za-z0-9_~.{}:@%+-]+/)+[A-Za-z0-9_~.{}:@%+/?=&-]*$')
DEX_MEMBER = re.compile(r'(?:.*/)?classes\d*\.dex$')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class DexAnnotations:
    """Read DEX identifiers and encoded annotations without decompiler guesses."""
    def __init__(self, data):
        if not data.startswith(b'dex\n'):
            raise ValueError('Unsupported DEX representation')
        self.data = data
        self.strings = []
        count, offset = struct.unpack_from('<II', data, 56)
        self.string_offsets = []
        for index in range(count):
            location = self.u32(offset + index * 4)
            _, location = self.uleb(location)
            self.string_offsets.append(location)
            self.strings.append(data[location:data.index(0, location)].decode('utf-8', 'replace'))
        count, offset = struct.unpack_from('<II', data, 64)
        self.types = [self.strings[self.u32(offset + index * 4)] for index in range(count)]
        count, offset = struct.unpack_from('<II', data, 72)
        self.prototypes = []
        for index in range(count):
            location = offset + index * 12
            parameters = self.u32(location + 8)
            argument_types = [] if not parameters else [
                self.types[self.u16(parameters + 4 + argument * 2)]
                for argument in range(self.u32(parameters))]
            self.prototypes.append('(' + ''.join(argument_types) + ')' + self.types[self.u32(location + 4)])
        count, offset = struct.unpack_from('<II', data, 88)
        self.methods = []
        for index in range(count):
            class_index, prototype_index, name_index = struct.unpack_from('<HHI', data, offset + index * 8)
            self.methods.append(self.types[class_index] + '->' + self.strings[name_index] + self.prototypes[prototype_index])

    def u16(self, offset):
        return struct.unpack_from('<H', self.data, offset)[0]

    def u32(self, offset):
        return struct.unpack_from('<I', self.data, offset)[0]

    def uleb(self, offset):
        value = shift = 0
        while True:
            byte = self.data[offset]
            offset += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value, offset
            shift += 7
            if shift > 35:
                raise ValueError('Invalid ULEB128')

    def annotation(self, offset):
        type_index, offset = self.uleb(offset)
        size, offset = self.uleb(offset)
        elements = {}
        for _ in range(size):
            name_index, offset = self.uleb(offset)
            elements[self.strings[name_index]], offset = self.value(offset)
        return {'type': self.types[type_index], 'elements': elements}, offset

    def value(self, offset):
        header = self.data[offset]
        offset += 1
        kind, argument = header & 31, header >> 5
        if kind == 0x1c:
            size, offset = self.uleb(offset)
            values = []
            for _ in range(size):
                value, offset = self.value(offset)
                values.append(value)
            return values, offset
        if kind == 0x1d:
            return self.annotation(offset)
        if kind == 0x1e:
            return None, offset
        if kind == 0x1f:
            return bool(argument), offset
        width = argument + 1
        value = int.from_bytes(self.data[offset:offset + width], 'little')
        offset += width
        if kind == 0x17:
            return self.strings[value], offset
        return {'encoded_type': kind, 'index_or_bits': value}, offset

    def request_annotations(self):
        count, offset = struct.unpack_from('<II', self.data, 96)
        for index in range(count):
            directory = self.u32(offset + index * 32 + 20)
            if not directory:
                continue
            field_count, method_count = struct.unpack_from('<II', self.data, directory + 4)
            method_entries = directory + 16 + field_count * 8
            for entry in range(method_count):
                method_index, annotation_set = struct.unpack_from('<II', self.data, method_entries + entry * 8)
                for annotation_index in range(self.u32(annotation_set)):
                    annotation_offset = self.u32(annotation_set + 4 + annotation_index * 4)
                    annotation, _ = self.annotation(annotation_offset + 1)
                    verb = HTTP_ANNOTATIONS.get(annotation['type'])
                    if not verb:
                        continue
                    elements = annotation['elements']
                    method = elements.get('method') if verb == 'HTTP' else verb
                    path = elements.get('path', '') if verb == 'HTTP' else elements.get('value', '')
                    if not isinstance(path, str) or not isinstance(method, str):
                        continue
                    yield {'method': method, 'path': path, 'declaring_method': self.methods[method_index],
                           'annotation_type': annotation['type'], 'annotation_byte_offset': annotation_offset,
                           'dynamic_url': not bool(path), 'evidence_kind': 'Retrofit method annotation'}


def url_candidate(value):
    if not value.startswith(('https://', 'http://')) or len(value) > 2048 or any(c.isspace() for c in value):
        return None
    try:
        parsed = urlsplit(value)
        if not parsed.hostname:
            return None
        # Query strings, fragments and userinfo are excluded from publishable output.
        return {'scheme': parsed.scheme, 'host': parsed.hostname, 'path': parsed.path,
                'raw_string_sha256': sha256(value.encode())}
    except ValueError:
        return None


def analyze(app):
    app_root = REPOSITORY_ROOT / 'apps' / app
    apk_directory = app_root / 'apks'
    inputs = sorted(apk_directory.glob('*.apk'))
    if not inputs or not (apk_directory / 'acquisition.json').is_file():
        raise ValueError(f'{app}: a completed APK acquisition is required')
    acquired = json.loads((apk_directory / 'acquisition.json').read_text())
    expected = {entry['name']: entry['sha256'] for entry in acquired['files']}
    if set(expected) != {path.name for path in inputs}:
        raise ValueError(f'{app}: APK set differs from acquisition receipt')
    def manifest_value(field):
        return subprocess.check_output(['apkanalyzer', 'manifest', field, str(apk_directory / 'base.apk')],
                                       text=True, stderr=subprocess.PIPE).strip()
    package, version = manifest_value('application-id'), manifest_value('version-name')
    if package != acquired['package']:
        raise ValueError(f'{app}: manifest package differs from acquisition receipt')
    inventory, dex_inventory, requests, urls, formats, errors, routes = [], [], [], [], [], [], []
    for apk in inputs:
        digest = sha256(apk.read_bytes())
        if digest != expected[apk.name]:
            raise ValueError(f'{app}: APK digest differs from verified acquisition')
        inventory.append({'name': apk.name, 'bytes': apk.stat().st_size, 'sha256': digest})
        with zipfile.ZipFile(apk) as archive:
            for member in archive.infolist():
                name = member.filename
                if name.endswith(('.bundle', '.hbc', '.js')) or name.startswith('lib/') and name.endswith('.so'):
                    header = archive.read(member)[:16]
                    representation = 'native ELF' if header.startswith(b'\x7fELF') else 'Hermes bytecode' if header.startswith(bytes.fromhex('c61fbc03c103191f')) else 'unclassified code asset'
                    formats.append({'apk': apk.name, 'member': name, 'bytes': member.file_size, 'representation': representation})
                if not DEX_MEMBER.fullmatch(name):
                    continue
                data = archive.read(member)
                try:
                    dex = DexAnnotations(data)
                    dex_inventory.append({'apk': apk.name, 'member': name, 'sha256': sha256(data),
                                          'strings': len(dex.strings), 'method_ids': len(dex.methods)})
                    for string_index, value in enumerate(dex.strings):
                        if len(value) <= 512 and ROUTE_LITERAL.fullmatch(value) and not value.startswith(('/data/', '/proc/', '/sys/', '/storage/', '/system/', '/dev/')):
                            routes.append({'path': value.split('?', 1)[0], 'raw_string_sha256': sha256(value.encode()),
                                           'apk': apk.name, 'dex': name, 'string_index': string_index,
                                           'string_byte_offset': dex.string_offsets[string_index], 'method': None})
                        candidate = url_candidate(value)
                        if candidate:
                            urls.append(candidate | {'apk': apk.name, 'dex': name, 'string_index': string_index,
                                                     'string_byte_offset': dex.string_offsets[string_index]})
                    for request in dex.request_annotations():
                        requests.append(request | {'apk': apk.name, 'dex': name})
                except (ValueError, IndexError, KeyError, struct.error) as error:
                    errors.append({'apk': apk.name, 'member': name, 'error_type': type(error).__name__})
        print(f'{app}: indexed {apk.name}', flush=True)
    result = {'schema_version': 1, 'app': app, 'package': package, 'version': version,
              'inputs': inventory, 'dex_inventory': dex_inventory, 'code_assets': formats,
              'request_declarations': requests, 'url_candidates': urls, 'route_candidates': routes, 'errors': errors,
              'stats': {'apk_files': len(inventory), 'dex_files': len(dex_inventory),
                        'dex_strings': sum(item['strings'] for item in dex_inventory),
                        'request_declarations': len(requests),
                        'distinct_literal_method_paths': len({(r['method'], r['path']) for r in requests if r['path']}),
                        'url_candidates': len(urls), 'route_candidates': len(routes), 'errors': len(errors)},
              'limitations': ['Annotations establish declarations, not invocation, server behavior, authentication, or working endpoints.',
                              'Relative paths are not bound to a host or base path. Empty paths require dynamic URL analysis.',
                              'Third-party libraries and unused code are included; declarations are not all first-party app APIs.',
                              'DEX annotation and literal URL scan only. Native, JavaScript/Hermes, generated and server-driven routes remain untraced.',
                              'No HTTP methods inferred from URL strings. No API requests or account access performed.',
                              'Query strings, fragments and userinfo are omitted from URL candidate output.']}
    destination = app_root / 'evidence' / 'static-analysis.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'app': app, 'version': version, **result['stats']}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apps', nargs='+', choices=['discord', 'tiktok', 'snapchat', 'roblox'])
    arguments = parser.parse_args()
    for app in arguments.apps:
        analyze(app)


if __name__ == '__main__':
    main()
