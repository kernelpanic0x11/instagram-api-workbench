#!/usr/bin/env python3
"""Reproduce pinned caller, parser and callback evidence for three bounded reads.

This script only reads the APK. It never connects to an account or executes app
code. The large shared onClick handler is retained only around the reviewed
request; all other selected methods retain their complete instruction stream.
"""
import argparse
import hashlib
import importlib.util
import json
import re
import zipfile
from pathlib import Path
from extract import Dex, DEFAULT_PROFILE, load_profile, sig
from literal_keys import literal_switch_cases

DIRECTORY = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location('shared', DIRECTORY / 'trace-shared-contracts.py')
shared = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(shared)
METHOD_RANGES = {
    'LX/0IoB;->A00(Lcom/instagram/common/session/UserSession;LX/0JQA;)LX/02sG;': None,
    'LX/0L1j;->A02(Landroid/content/Context;LX/05B6;Lcom/instagram/common/session/UserSession;)V': None,
    'LX/0LMw;->onClick(Landroid/view/View;)V': [(0x357, 0x37f)],
    'LX/0221;->A0K(LX/02rr;LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;': None,
    'LX/0224;->A0P(LX/04x5;Ljava/lang/String;)LX/02sG;': None,
    'LX/02rr;->A03(LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;': None,
    'LX/02rr;->A04(LX/0Wvm;Lcom/instagram/common/session/UserSession;I)LX/02sB;': None,
    'LX/0dja;->unsafeParseFromJson(LX/04s3;)Ljava/lang/Object;': None,
    'LX/0dmv;->unsafeParseFromJson(LX/04s3;)Ljava/lang/Object;': None,
    'LX/0Ew3;->unsafeParseFromJson(LX/04s3;)Ljava/lang/Object;': None,
    'LX/0HKd;->A0p(Lcom/instagram/common/session/UserSession;Ljava/lang/Object;)V': None,
    'LX/0EoX;->A0k(Ljava/lang/Object;)V': None,
    'LX/0Enc;->A0k(Ljava/lang/Object;)V': None,
    'LX/0LDK;->A01(LX/0LDK;Ljava/lang/Integer;Ljava/lang/String;I)V': None,
}
REVIEWED_ROUTES = [
    '/accounts/get_presence_disabled/',
    '/users/get_recommendation_status_nudge/',
    '/business/account/get_meta_verified_for_business_info/',
]


def collect(apk):
    with apk.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != load_profile(DEFAULT_PROFILE)['apk_sha256']:
        raise ValueError('APK differs from the pinned reviewed input')
    methods, literal_keys = {}, []
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r'classes\d*\.dex', name):
                continue
            data = archive.read(name)
            dex = Dex(data, name)
            dex_hash = hashlib.sha256(data).hexdigest()
            for method_index, code in dex.codes():
                selector = sig(dex.methods[method_index])
                if selector == 'LX/020R;->A00(I)Ljava/lang/String;':
                    case = literal_switch_cases(dex, method_index, code).get(0xb2)
                    if not case or case['value'] != 'copresence_disabled':
                        raise ValueError('Reviewed presence key no longer matches')
                    case['proof']['dex_sha256'] = dex_hash
                    literal_keys.append(case)
                if selector not in METHOD_RANGES:
                    continue
                evidence = shared.proof(dex, method_index, code, dex_hash)
                evidence['method_index'] = method_index
                ranges = METHOD_RANGES[selector]
                if ranges:
                    evidence['instruction_scope'] = 'reviewed-request-block-only'
                    evidence['code_unit_ranges'] = [{'start': start, 'end_exclusive': end} for start, end in ranges]
                    evidence['instructions'] = [instruction for instruction in evidence['instructions']
                        if any(start <= instruction['code_unit_offset'] < end for start, end in ranges)]
                else:
                    evidence['instruction_scope'] = 'complete-method'
                methods[selector] = evidence
    if set(methods) != set(METHOD_RANGES) or len(literal_keys) != 1:
        raise ValueError('Reviewed read evidence is incomplete')
    return {
        'source_apk_sha256': digest,
        'scope': 'Static construction and client response handling for three bounded GET reads. No runtime data or account values.',
        'reviewed_routes': REVIEWED_ROUTES,
        'methods': methods,
        'literal_keys': literal_keys,
        'shared_finalization_evidence': 'shared-contracts.json',
        'limitations': [
            'Client construction does not establish exhaustive server behavior or requiredness.',
            'Shared optional device configuration and authenticated transport context may affect requests.',
            'Callback side effects are inspected as context; the direct HTTP probe executes no client callback, Bloks request or confirmation action.',
            'Only the identified request block of the large shared onClick method is included.',
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, default=DIRECTORY.parents[1] / 'apks/base.apk')
    parser.add_argument('--output', type=Path, default=DIRECTORY / 'reviewed-read-evidence.json')
    arguments = parser.parse_args()
    result = collect(arguments.apk)
    arguments.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'reviewed_routes': len(result['reviewed_routes']), 'reviewed_methods': len(result['methods'])}))
