#!/usr/bin/env python3
"""Retain selected request-factory instructions for reviewing TikTok's obfuscated annotations."""
import importlib.util
import json
import zipfile
from pathlib import Path
from research_inputs import verified_apk

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dex_trace', ROOT / 'scripts/trace-dex-candidates.py')
trace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)
SELECTORS = {
    'Lcom/bytedance/retrofit2/RequestFactory;': {'parseAnnotations', '<init>', 'create'},
    'LX/04zq;': {'LIZLLL'},
}


def main():
    records = []
    apk = verified_apk('tiktok', 'base.apk')
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not trace.annotation_reader.DEX_MEMBER.fullmatch(name):
                continue
            dex = trace.instruction_reader.Dex(archive.read(name), name)
            if not any(owner in dex.types for owner in SELECTORS):
                continue
            for method_id, code in dex.codes():
                owner, method_name, _ = dex.methods[method_id]
                if method_name not in SELECTORS.get(owner, set()):
                    continue
                instructions, _ = dex.insns(code)
                decoded = [trace.instruction_record(dex, instruction) for instruction in instructions]
                positions = set()
                for index, instruction in enumerate(decoded):
                    relevant = instruction.get('string') == 'GET' or instruction.get('referenced_type') == 'LX/050z;'
                    relevant |= instruction.get('callee', '').startswith(('LX/050z;->value(', 'LX/04zq;->LIZLLL(', 'Lcom/bytedance/retrofit2/RequestBuilder;-><init>('))
                    field = instruction.get('field', [])
                    relevant |= bool(field and field[1] in ('httpMethod', 'relativeUrl', 'LJIJJLI', 'LJJIFFI'))
                    if relevant:
                        positions.update(range(max(0, index - 3), min(len(decoded), index + 7)))
                records.append({'apk': 'base.apk', 'dex': name,
                                'declaring_method': trace.instruction_reader.sig(dex.methods[method_id]),
                                'instructions': [decoded[index] for index in sorted(positions)]})
    result = {'app': 'tiktok', 'evidence_kind': 'selected DEX request-factory instruction excerpts', 'methods': records,
              'limitations': ['Excerpts support manual review. They are not an automatic control-flow or register-dataflow proof.',
                              'The obfuscated selectors are bound to the APK hashes in static-analysis.json and must not be reused on a different version.']}
    (ROOT / 'apps/tiktok/evidence/request-factory-trace.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'methods_retained': len(records)}))


if __name__ == '__main__':
    main()
