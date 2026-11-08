#!/usr/bin/env python3
"""Enable an APK's debug overrides and optionally give it a clone package.

This changes only android:debuggable from false to true in the compiled
AndroidManifest.xml unless --clone-package is supplied. Clone mode also renames
the manifest package, provider authorities, app-defined permissions, and task
affinities without renaming Java component classes. It does not add trust
anchors or remove pinning code.
"""
import argparse
import re
import struct
import sys
import zipfile
from pathlib import Path


RES_STRING_POOL_TYPE = 0x0001
RES_XML_RESOURCE_MAP_TYPE = 0x0180
RES_XML_START_ELEMENT_TYPE = 0x0102
TYPE_INT_BOOLEAN = 0x12
TYPE_STRING = 0x03
ANDROID_DEBUGGABLE = 0x0101000F
UTF8_FLAG = 0x00000100
NO_INDEX = 0xFFFFFFFF


class PatchError(ValueError):
    pass


def chunks(data, start=0):
    offset = start
    while offset + 8 <= len(data):
        chunk_type, header_size, size = struct.unpack_from('<HHI', data, offset)
        if header_size < 8 or size < header_size or offset + size > len(data):
            raise PatchError(f'invalid binary XML chunk at offset {offset}')
        yield offset, chunk_type, header_size, size
        offset += size
    if offset != len(data):
        raise PatchError('trailing bytes after final binary XML chunk')


def _length8(data, offset):
    first = data[offset]
    if first & 0x80:
        return ((first & 0x7F) << 8) | data[offset + 1], 2
    return first, 1


def _length16(data, offset):
    first = struct.unpack_from('<H', data, offset)[0]
    if first & 0x8000:
        second = struct.unpack_from('<H', data, offset + 2)[0]
        return ((first & 0x7FFF) << 16) | second, 4
    return first, 2


def _encode_length8(length):
    if length > 0x7FFF:
        raise PatchError('UTF-8 manifest string is too long')
    if length > 0x7F:
        return bytes((0x80 | (length >> 8), length & 0xFF))
    return bytes((length,))


def _encode_length16(length):
    if length > 0x7FFFFFFF:
        raise PatchError('UTF-16 manifest string is too long')
    if length > 0x7FFF:
        return struct.pack('<HH', 0x8000 | (length >> 16), length & 0xFFFF)
    return struct.pack('<H', length)


def read_string_pool(data):
    xml_header_size = struct.unpack_from('<H', data, 2)[0]
    for offset, chunk_type, header_size, size in chunks(data, xml_header_size):
        if chunk_type != RES_STRING_POOL_TYPE:
            continue
        if header_size < 28:
            raise PatchError('invalid binary XML string pool header')
        string_count, style_count, flags, strings_start, styles_start = struct.unpack_from(
            '<IIIII', data, offset + 8
        )
        if style_count:
            raise PatchError('styled manifest string pools are not supported')
        offsets = struct.unpack_from(f'<{string_count}I', data, offset + header_size)
        values = []
        utf8 = bool(flags & UTF8_FLAG)
        for relative in offsets:
            position = offset + strings_start + relative
            if utf8:
                _, first_size = _length8(data, position)
                byte_length, second_size = _length8(data, position + first_size)
                start = position + first_size + second_size
                values.append(bytes(data[start:start + byte_length]).decode('utf-8'))
            else:
                char_length, prefix_size = _length16(data, position)
                start = position + prefix_size
                values.append(bytes(data[start:start + char_length * 2]).decode('utf-16le'))
        return {
            'offset': offset,
            'header_size': header_size,
            'size': size,
            'string_count': string_count,
            'flags': flags,
            'strings_start': strings_start,
            'styles_start': styles_start,
            'values': values,
        }
    raise PatchError('manifest has no binary XML string pool')


def replace_string_pool(data, pool, replacements):
    values = list(pool['values'])
    for index, value in replacements.items():
        values[index] = value
    utf8 = bool(pool['flags'] & UTF8_FLAG)
    encoded = []
    for value in values:
        if utf8:
            payload = value.encode('utf-8')
            utf16_length = len(value.encode('utf-16le')) // 2
            encoded.append(_encode_length8(utf16_length) + _encode_length8(len(payload)) + payload + b'\0')
        else:
            payload = value.encode('utf-16le')
            encoded.append(_encode_length16(len(payload) // 2) + payload + b'\0\0')
    offsets = []
    string_data = bytearray()
    for value in encoded:
        offsets.append(len(string_data))
        string_data.extend(value)
    string_data.extend(b'\0' * ((-len(string_data)) % 4))

    offset = pool['offset']
    old_size = pool['size']
    prefix = bytearray(data[offset:offset + pool['strings_start']])
    struct.pack_into(f'<{len(offsets)}I', prefix, pool['header_size'], *offsets)
    struct.pack_into('<I', prefix, 20, pool['strings_start'])
    struct.pack_into('<I', prefix, 24, 0)
    new_chunk = prefix + string_data
    struct.pack_into('<I', new_chunk, 4, len(new_chunk))
    rebuilt = bytearray(data[:offset]) + new_chunk + bytearray(data[offset + old_size:])
    struct.pack_into('<I', rebuilt, 4, len(rebuilt))
    return rebuilt


def clone_replacements(data, pool, clone_package):
    strings = pool['values']
    replacements = {}
    source_package = None
    permission_elements = {'permission', 'permission-group', 'permission-tree', 'uses-permission'}
    renamed_attributes = {'authorities', 'permission', 'readPermission', 'writePermission', 'taskAffinity'}
    xml_header_size = struct.unpack_from('<H', data, 2)[0]
    for offset, chunk_type, header_size, size in chunks(data, xml_header_size):
        if chunk_type != RES_XML_START_ELEMENT_TYPE:
            continue
        attr_ext = offset + header_size
        element_index = struct.unpack_from('<I', data, attr_ext + 4)[0]
        element = strings[element_index]
        attribute_start, attribute_size, attribute_count = struct.unpack_from('<HHH', data, attr_ext + 8)
        first_attribute = attr_ext + attribute_start
        for index in range(attribute_count):
            attribute = first_attribute + index * attribute_size
            name_index, raw_index = struct.unpack_from('<II', data, attribute + 4)
            _, _, value_type, value_data = struct.unpack_from('<HBBI', data, attribute + 12)
            value_index = raw_index if raw_index != NO_INDEX else value_data if value_type == TYPE_STRING else None
            if value_index is None or value_index >= len(strings):
                continue
            name = strings[name_index]
            value = strings[value_index]
            if element == 'manifest' and name == 'package':
                source_package = value
                replacements[value_index] = clone_package
                continue
            should_rename = name in renamed_attributes or (element in permission_elements and name == 'name')
            if should_rename and source_package and source_package in value:
                replacements[value_index] = value.replace(source_package, clone_package)
    if not source_package:
        raise PatchError('manifest package attribute was not found')
    if source_package == clone_package:
        raise PatchError('clone package matches the source package')
    return replacements


def patch_manifest(manifest, clone_package=None, enable_debuggable=True):
    data = bytearray(manifest)
    if len(data) < 8:
        raise PatchError('AndroidManifest.xml is not compiled binary XML')
    xml_type, xml_header_size, xml_size = struct.unpack_from('<HHI', data, 0)
    if xml_type != 0x0003 or xml_header_size != 8 or xml_size != len(data):
        raise PatchError('AndroidManifest.xml is not compiled binary XML')

    resource_ids = []
    element_chunks = []
    for offset, chunk_type, header_size, size in chunks(data, xml_header_size):
        if chunk_type == RES_XML_RESOURCE_MAP_TYPE:
            resource_ids = list(struct.unpack_from(
                f'<{(size - header_size) // 4}I', data, offset + header_size
            ))
        elif chunk_type == RES_XML_START_ELEMENT_TYPE:
            element_chunks.append((offset, header_size, size))

    if enable_debuggable:
        try:
            debuggable_name_index = resource_ids.index(ANDROID_DEBUGGABLE)
        except ValueError as exc:
            raise PatchError('manifest has no android:debuggable resource mapping') from exc

        matches = []
        for offset, header_size, size in element_chunks:
            if header_size < 16 or size < header_size + 20:
                raise PatchError('invalid start-element chunk')
            attr_ext = offset + header_size
            attribute_start, attribute_size, attribute_count = struct.unpack_from(
                '<HHH', data, attr_ext + 8
            )
            if attribute_size < 20:
                raise PatchError('unsupported compiled attribute size')
            first_attribute = attr_ext + attribute_start
            for index in range(attribute_count):
                attribute = first_attribute + index * attribute_size
                if attribute + 20 > offset + size:
                    raise PatchError('compiled attribute extends beyond its chunk')
                name_index = struct.unpack_from('<I', data, attribute + 4)[0]
                if name_index != debuggable_name_index:
                    continue
                value_size, value_res0, value_type, value_data = struct.unpack_from(
                    '<HBBI', data, attribute + 12
                )
                if value_size != 8 or value_res0 != 0 or value_type != TYPE_INT_BOOLEAN:
                    raise PatchError('android:debuggable is not a compiled boolean')
                matches.append((attribute + 16, value_data))

        if len(matches) != 1:
            raise PatchError(f'expected one android:debuggable attribute, found {len(matches)}')
        value_offset, old_value = matches[0]
        if old_value not in (0, 0xFFFFFFFF):
            raise PatchError(f'unexpected android:debuggable value: 0x{old_value:08x}')
        if old_value == 0xFFFFFFFF:
            raise PatchError('android:debuggable is already true; input was not changed')
        struct.pack_into('<I', data, value_offset, 0xFFFFFFFF)
    if clone_package:
        pool = read_string_pool(data)
        replacements = clone_replacements(data, pool, clone_package)
        data = replace_string_pool(data, pool, replacements)
    return bytes(data)


def patch_apk(source, destination, clone_package=None, enable_debuggable=True):
    if source.resolve() == destination.resolve():
        raise PatchError('refusing to overwrite the input APK')
    if destination.exists():
        raise PatchError(f'refusing to overwrite existing output: {destination}')
    try:
        with zipfile.ZipFile(source, 'r') as apk:
            manifest = apk.read('AndroidManifest.xml')
            info = apk.getinfo('AndroidManifest.xml')
            patched = patch_manifest(manifest, clone_package, enable_debuggable)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(destination, 'w', allowZip64=True) as output:
                for entry in apk.infolist():
                    if entry.filename.upper().startswith('META-INF/'):
                        continue
                    output.writestr(entry, patched if entry.filename == info.filename else apk.read(entry.filename))
    except KeyError as exc:
        destination.unlink(missing_ok=True)
        raise PatchError('APK has no AndroidManifest.xml') from exc
    except (OSError, zipfile.BadZipFile):
        destination.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clone-package')
    parser.add_argument('--no-debuggable', action='store_true', help='Rename only; use for split APKs')
    parser.add_argument('input_apk', type=Path)
    parser.add_argument('output_apk', type=Path)
    args = parser.parse_args()
    if args.clone_package and not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+', args.clone_package):
        parser.error('--clone-package must be a dotted Android package name')
    try:
        patch_apk(args.input_apk, args.output_apk, args.clone_package, not args.no_debuggable)
    except (OSError, zipfile.BadZipFile, PatchError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    print(args.output_apk)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
