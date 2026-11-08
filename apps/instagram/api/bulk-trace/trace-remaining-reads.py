#!/usr/bin/env python3
"""Bind the frozen remaining-read review to pinned caller and key-decoder bytecode."""
import importlib.util
import json
import struct
import zipfile
from pathlib import Path
from extract import Dex, sig

DIRECTORY = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location('shared', DIRECTORY / 'trace-shared-contracts.py')
shared = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(shared)
KEY_CASES = {
    'LX/0021;': {0x140: 'media_infos'},
    'LX/0C4G;': {0x44f: 'compound_product_ids', 0x584: 'tagged_products'},
    'LX/0000;': {0x5ff: 'page_type', 0x38e: 'should_disable_exposures',
                 0xb9: 'music_browse_session_id', 0x2a1: 'browse_session_full_id'},
    'LX/0005;': {0x40: 'horizon_world_id'},
    'LX/0018;': {0x7f: 'user_fbid'},
    'LX/020R;': {0x44d: 'include_social_context'},
}
EXTRA_METHODS = {
    ('LX/0aCY;', 'A01', '(LX/0bfb;Lcom/instagram/shopping/model/taggingfeed/ShoppingTaggingFeedClientState;Ljava/lang/Integer;Ljava/lang/String;Ljava/util/List;Ljava/util/List;)Lcom/instagram/shopping/intf/taggingfeed/ShoppingTaggingFeedArguments;'),
    ('LX/0C5K;', 'G6h', '(Landroid/view/View;LX/0HWh;LX/02G1;I)V'),
    ('LX/0C5K;', '<init>', '(Landroidx/fragment/app/FragmentActivity;LX/00ez;LX/05B6;LX/0Eto;Lcom/instagram/common/session/UserSession;LX/0Fmo;LX/0Wny;LX/0Wym;LX/0C22;LX/0C6K;LX/0C1Y;)V'),
    ('LX/0BwH;', 'invoke', '()Ljava/lang/Object;'),
    ('LX/0465;', 'A0r', '(LX/0C5K;)Ljava/lang/String;'),
    ('LX/0BSU;', 'invoke', '()Ljava/lang/Object;'),
    ('Lcom/instagram/newsfeed/fragment/NewsfeedYouComposeFragment;', '<init>', '()V'),
    ('Lcom/instagram/newsfeed/fragment/NewsfeedYouComposeFragment;', 'A00', '(Lcom/instagram/newsfeed/fragment/NewsfeedYouComposeFragment;)LX/03pA;'),
    ('LX/03pA;', '<init>', '(Ljava/lang/String;)V'),
    ('LX/03pA;', '<init>', '(LX/0dbC;Ljava/lang/Class;Ljava/lang/String;)V'),
    ('LX/03pA;', 'getModuleName', '()Ljava/lang/String;'),
    ('LX/0bfb;', '<clinit>', '()V'),
    ('LX/06Rj;', '<clinit>', '()V'), ('LX/06Rj;', 'A00', '()Ljava/lang/String;'),
    ('LX/06Rj;', 'A01', '(III)Ljava/lang/String;'),
    ('LX/03ld;', 'A00', '()J'),
    ('LX/0RNE;', 'A00', '(LX/04s2;Lcom/instagram/shopping/model/taggingfeed/ShoppingTaggingFeedClientState;)V'),
    ('Lcom/instagram/shopping/intf/taggingfeed/ShoppingTaggingFeedArguments;', '<init>', '(Lcom/instagram/pendingmedia/model/ClipInfo;LX/0bfb;Lcom/instagram/shopping/model/taggingfeed/ShoppingTaggingFeedClientState;Lcom/instagram/shopping/model/taggingfeed/ShoppingTaggingFeedHeader;Lcom/instagram/shopping/model/taggingfeed/TaggingFeedMultiSelectState;Lcom/instagram/user/model/Product;Ljava/lang/Double;Ljava/lang/Integer;Ljava/lang/Long;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/util/List;Ljava/util/List;Ljava/util/List;ZZZZZ)V'),
    ('Lcom/instagram/shopping/model/taggingfeed/ShoppingTaggingFeedClientState;', '<init>', '()V'),
    ('Lcom/instagram/shopping/model/taggingfeed/ShoppingTaggingFeedClientState;', '<init>', '(Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;Ljava/util/List;)V'),
    ('LX/0o9z;', 'invoke', '()Ljava/lang/Object;'),
    ('Lcom/instagram/shopping/repository/taggingfeed/ShoppingTaggingFeedRepository;', 'A03', '()LX/0VYi;'),
    ('Lcom/instagram/shopping/repository/taggingfeed/ShoppingTaggingFeedRepository;', 'A04', '(Ljava/lang/String;)LX/0VYi;'),
    ('LX/0367;', '<clinit>', '()V'), ('LX/0367;', 'A01', '()Ljava/lang/String;'),
    ('LX/0367;', 'A02', '(III)Ljava/lang/String;'),
    ('LX/0JLG;', 'onCreate', '(Landroid/os/Bundle;)V'),
    ('Lcom/instagram/user/model/User;', 'A7Y', '()Ljava/lang/String;'),
    ('LX/01FG;', 'GeO', '(LX/0FaK;LX/04Qu;Ljava/util/List;Ljava/util/Map;LX/0ymj;LX/0ymj;Lkotlin/jvm/functions/Function3;Z)LX/0FdQ;'),
    ('LX/05wo;', 'unsafeParseFromJson', '(LX/04s3;)Ljava/lang/Object;'),
    ('LX/0o8B;', 'A01', '(LX/04x5;LX/05Dd;Ljava/lang/String;Ljava/lang/String;Z)LX/02sG;'),
    ('LX/0R73;', '<clinit>', '()V'), ('LX/0R73;', 'A00', '(III)Ljava/lang/String;'),
    ('LX/05Ee;', 'A03', '(Landroid/content/Context;)Ljava/lang/String;'),
    ('LX/05Ed;', 'A01', '(Ljava/io/File;Ljava/io/File;)Ljava/lang/String;'),
    ('LX/02df;', 'A04', '(LX/02dl;)Ljava/lang/String;'),
    ('LX/0F4v;', 'Co4', '()Ljava/lang/String;'),
    ('LX/0F4v;', 'onViewCreated', '(Landroid/view/View;Landroid/os/Bundle;)V'),
    ('LX/0D2x;', 'invoke', '()Ljava/lang/Object;'),
    ('LX/02bJ;', 'A02', '(Lcom/instagram/common/session/UserSession;Lkotlin/jvm/functions/Function0;)Ljava/lang/Object;'),
    ('LX/0F4w;', '<init>', '(Landroid/view/View;LX/00ez;LX/0Aqy;Lcom/google/common/collect/ImmutableList;Lcom/google/common/collect/ImmutableList;LX/06Sv;Lcom/instagram/common/session/UserSession;LX/028Y;LX/0B0D;LX/0nbi;LX/0naF;LX/0F6V;LX/02AS;Linstagram/core/camera/CaptureState;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;ZZZZZZZZ)V'),
    ('LX/0F4w;', 'A02', '(LX/0F7a;)Landroidx/fragment/app/Fragment;'),
    ('LX/0YQE;', 'onCreate', '(Landroid/os/Bundle;)V'),
    ('LX/0ClR;', 'A01', '(Landroid/os/Bundle;Ljava/lang/String;)Ljava/lang/String;'),
    ('LX/06Sv;', '<clinit>', '()V'),
    ('Lcom/instagram/fanclub/promovideo/FanClubPromoAndWelcomeVideoApi;', 'A01', '(LX/0Pmx;)Ljava/lang/Object;'),
    ('Lcom/instagram/user/model/User;', 'A0r', '()Lcom/instagram/api/schemas/FanClubInfoDict;'),
    ('Lcom/instagram/api/schemas/ImmutablePandoFanClubInfoDict;', 'C9p', '()Ljava/lang/String;'),
    ('Lcom/instagram/api/schemas/FanClubInfoDictImpl;', 'C9p', '()Ljava/lang/String;'),
    ('LX/02A2;', 'A00', '(LX/04s2;Lcom/instagram/api/schemas/FanClubInfoDictImpl;)V'),
    ('LX/0Hqg;', 'B4p', '(Ljava/lang/String;Ljava/lang/String;)LX/09AD;'),
    ('LX/0Dlh;', '<init>', '(Lcom/instagram/common/session/UserSession;)V'),
    ('LX/0BWF;', 'A05', '(LX/0BWF;)Ljava/lang/Object;'),
    ('LX/0ECb;', 'onCreate', '(Landroid/os/Bundle;)V'),
    ('LX/0ZwX;', 'A02', '()LX/00fh;'),
    ('LX/0JTl;', 'A00', '(LX/06Sv;)Ljava/lang/String;'),
    ('LX/0bkh;', '<clinit>', '()V'), ('LX/0bkh;', 'toString', '()Ljava/lang/String;'),
    ('LX/02l6;', '<clinit>', '()V'), ('LX/02l6;', 'toString', '()Ljava/lang/String;'),
    ('LX/0123;', 'A0s', '()Ljava/lang/String;'),
} | {
    ('LX/0241;', '<clinit>', '()V'), ('LX/0241;', 'A00', '()Ljava/lang/String;'),
    ('LX/0241;', 'A01', '(III)Ljava/lang/String;'),
    ('LX/0242;', '<clinit>', '()V'), ('LX/0242;', 'A01', '()Ljava/lang/String;'),
    ('LX/0242;', 'A05', '(III)Ljava/lang/String;'),
}


def selector(signature):
    owner, tail = signature.split('->', 1)
    name, descriptor = tail.split('(', 1)
    return owner, name, '(' + descriptor


def switch_case_proof(dex, code, expected):
    """Retain only a reviewed packed-switch edge and its literal return, not the string table."""
    instructions = {pc: (word, opcode, width, offset) for pc, word, opcode, width, offset in dex.insns(code)[0]}
    result = []
    for pc, (word, opcode, width, offset) in instructions.items():
        if opcode != 0x2b:
            continue
        payload_pc = pc + struct.unpack_from('<i', dex.d, offset + 2)[0]
        payload = code + 16 + 2 * payload_pc
        if dex.u16(payload) != 0x100:
            raise ValueError('Expected packed-switch payload')
        size = dex.u16(payload + 2)
        first = struct.unpack_from('<i', dex.d, payload + 4)[0]
        for index, value in expected.items():
            if not first <= index < first + size:
                continue
            entry_offset = payload + 8 + 4 * (index - first)
            target_pc = pc + struct.unpack_from('<i', dex.d, entry_offset)[0]
            literal_word, literal_opcode, literal_width, literal_offset = instructions[target_pc]
            if literal_opcode not in (0x1a, 0x1b):
                raise ValueError('Reviewed case must immediately load its literal')
            string_index = dex.u16(literal_offset + 2) if literal_opcode == 0x1a else dex.u32(literal_offset + 2)
            return_word, return_opcode, _, return_offset = instructions[target_pc + literal_width]
            if dex.strings[string_index] != value or return_opcode != 0x11 or return_word >> 8 != literal_word >> 8:
                raise ValueError('Reviewed literal return differs')
            result.append({'index': index, 'value': value, 'switch_code_unit_offset': pc,
                           'switch_code_units': [dex.u16(offset + 2*i) for i in range(width)],
                           'payload_byte_offset': payload, 'payload_header_code_units': [dex.u16(payload + 2*i) for i in range(4)],
                           'entry_byte_offset': entry_offset, 'entry_code_units': [dex.u16(entry_offset), dex.u16(entry_offset + 2)],
                           'target_code_unit_offset': target_pc,
                           'literal_code_units': [dex.u16(literal_offset + 2*i) for i in range(literal_width)],
                           'return_code_unit': dex.u16(return_offset)})
    if len(result) != len(expected):
        raise ValueError('Missing reviewed switch case')
    return result


def main():
    review = json.loads((DIRECTORY.parent / 'remaining-read-review.json').read_text())
    shared.SELECTORS |= EXTRA_METHODS | {selector(caller) for operation in review['operations'] for caller in operation['callers']}
    apk = DIRECTORY.parents[1] / 'apks/base.apk'
    result = shared.collect(apk)
    if result['source_apk_sha256'] != review['source_apk_sha256']:
        raise ValueError('Review provenance differs')
    result.pop('rules', None)
    missing = {caller for operation in review['operations'] for caller in operation['callers']} - result['methods'].keys()
    if missing:
        raise ValueError('Reviewed caller proof unavailable')
    result['reviewed_routes'] = [operation['path'] for operation in review['operations']]
    result['key_decoders'] = {}
    with zipfile.ZipFile(apk) as archive:
        for name in archive.namelist():
            if not name.startswith('classes') or not name.endswith('.dex'):
                continue
            dex = Dex(archive.read(name), name)
            for method_index, code in dex.codes():
                owner, method, descriptor = dex.methods[method_index]
                if owner not in KEY_CASES or method != 'A00' or descriptor != '(I)Ljava/lang/String;':
                    continue
                result['key_decoders'][sig(dex.methods[method_index])] = {
                    'dex': name, 'code_item_byte_offset': code,
                    'cases': switch_case_proof(dex, code, KEY_CASES[owner])}
    if len(result['key_decoders']) != len(KEY_CASES):
        raise ValueError('Decoder proof unavailable')
    (DIRECTORY / 'remaining-read-evidence.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'reviewedRoutes': len(result['reviewed_routes']), 'callerAndHelperMethods': len(result['methods']), 'decodedKeys': sum(len(p['cases']) for p in result['key_decoders'].values())}))


if __name__ == '__main__':
    main()
