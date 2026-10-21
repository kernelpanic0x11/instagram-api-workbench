#!/usr/bin/env python3
"""Find Roblox ELF constants and direct ARM64 address-forming references.

No function names or HTTP semantics are inferred from string proximity.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
from research_inputs import extract_member
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Elf64:
    def __init__(self, data):
        if data[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<H', data, 18)[0] != 183:
            raise ValueError('Expected little-endian ARM64 ELF64')
        self.data = data
        section_offset = struct.unpack_from('<Q', data, 40)[0]
        width, count, names_index = struct.unpack_from('<HHH', data, 58)
        sections = [struct.unpack_from('<IIQQQQIIQQ', data, section_offset + index * width) for index in range(count)]
        names = sections[names_index]
        name_data = data[names[4]:names[4] + names[5]]
        self.sections = {}
        for section in sections:
            name = name_data[section[0]:name_data.index(0, section[0])].decode('ascii', 'replace')
            self.sections[name] = {'type': section[1], 'address': section[3], 'offset': section[4], 'size': section[5]}

    def bytes(self, name):
        section = self.sections[name]
        return self.data[section['offset']:section['offset'] + section['size']]


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def direct_address_pairs(text, start_address, targets):
    """Recognize adjacent ADRP/ADD instructions, preserving exact virtual addresses."""
    for offset in range(0, len(text) - 7, 4):
        instruction, following = struct.unpack_from('<II', text, offset)
        if instruction & 0x9f000000 != 0x90000000:
            continue
        if following & 0xff800000 != 0x91000000:
            continue
        register = instruction & 31
        source_register = (following >> 5) & 31
        if register == 31 or source_register != register:
            continue
        immediate = ((instruction >> 29) & 3) | (((instruction >> 5) & 0x7ffff) << 2)
        pc = start_address + offset
        page = (pc & ~4095) + (signed(immediate, 21) << 12)
        addition = ((following >> 10) & 4095) << (12 if following & (1 << 22) else 0)
        address = page + addition
        if address in targets:
            yield {'instruction_virtual_address': pc, 'target_virtual_address': address,
                   'instruction_words': [hex(instruction), hex(following)], 'kind': 'adjacent ADRP/ADD address formation'}


def trace(objdump):
    library = extract_member('roblox', 'split_config.arm64_v8a.apk', 'lib/arm64-v8a/libroblox.so', 'libroblox.so')
    data = library.read_bytes()
    elf = Elf64(data)
    constants = []
    for name in ('.rodata', '.data.rel.ro'):
        if name not in elf.sections:
            continue
        section = elf.sections[name]
        content = elf.bytes(name)
        for match in re.finditer(rb'[\x20-\x7e]{4,2048}', content):
            value = match.group().decode('ascii')
            relevant_url = False
            if value.startswith(('https://', 'http://')):
                try:
                    host = urlsplit(value).hostname or ''
                    relevant_url = host == 'roblox.com' or host.endswith('.roblox.com')
                except ValueError:
                    pass
            if not relevant_url and value not in {'HttpService', 'HttpRequest', 'HttpRequest::send', 'Http::get', 'Http::post'}:
                continue
            if relevant_url:
                parsed = urlsplit(value)
                published_value = parsed.scheme + '://' + (parsed.hostname or '') + parsed.path
            else:
                published_value = value
            constants.append({'section': name, 'value': published_value,
                              'raw_string_sha256': hashlib.sha256(match.group()).hexdigest(),
                              'file_offset': section['offset'] + match.start(),
                              'virtual_address': section['address'] + match.start()})
    targets = {constant['virtual_address']: constant for constant in constants}
    references = list(direct_address_pairs(elf.bytes('.text'), elf.sections['.text']['address'], targets))
    for reference in references:
        reference['constant'] = targets[reference['target_virtual_address']]['value']
    # Keep precise disassembly excerpts for a small, deterministic selection.
    selected = [item for item in references if item['constant'] == 'HttpService'][:4]
    selected += [item for item in references if item['constant'].startswith('https://apis.roblox.com')][:4]
    selected += references[:4]
    for reference in selected:
        address = reference['instruction_virtual_address']
        output = subprocess.check_output([str(objdump), '-d', '--no-show-raw-insn',
                                          f'--start-address={max(0, address - 16)}', f'--stop-address={address + 32}', str(library)], text=True)
        reference['assembly'] = [line.strip() for line in output.splitlines() if re.match(r'^\s*[0-9a-f]+:', line)]
    symbols = subprocess.check_output([str(objdump), '--dynamic-syms', str(library)], text=True)
    exported_network_symbols = [line.strip() for line in symbols.splitlines()
                                if re.search(r'NativeSettingsInterface_nativeSetHttpClientProxy|NativeGLInterface_reportNetworkStateChanged', line)]
    result = {'app': 'roblox', 'source_apk': 'split_config.arm64_v8a.apk',
              'source_member': 'lib/arm64-v8a/libroblox.so', 'library_sha256': hashlib.sha256(data).hexdigest(),
              'tool': subprocess.check_output([str(objdump), '--version'], text=True).splitlines()[0],
              'sections': elf.sections, 'constants': constants, 'address_references': references,
              'exported_network_symbols': exported_network_symbols,
              'stats': {'first_party_url_or_http_constants': len(constants), 'direct_address_references': len(references)},
              'limitations': ['Only selected printable strings in .rodata/.data.rel.ro and adjacent ARM64 ADRP/ADD pairs are inspected.',
                              'String address formation is not proof of request execution, HTTP method, payload, host binding or call graph.',
                              'Indirect loads, non-adjacent pairs, dynamic strings, other code sections and libraries are outside this pass.',
                              'Exported JNI names establish bridge symbols only. Stripped internal function names are not reconstructed.',
                              'No runtime instrumentation, API requests, or account storage accessed.']}
    (ROOT / 'apps/roblox/evidence/native-trace.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['stats']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--objdump', type=Path, default=Path('/opt/homebrew/opt/llvm/bin/llvm-objdump'))
    trace(parser.parse_args().objdump)


if __name__ == '__main__':
    main()
