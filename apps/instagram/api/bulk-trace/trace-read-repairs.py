#!/usr/bin/env python3
"""Publish APK-bound instruction proofs for reviewed HTTP-400 reads."""
import importlib.util
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('shared', DIRECTORY / 'trace-shared-contracts.py')
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
ROUTES = {
    '/dynamic_onboarding/get_direct_empty_state/', '/api/v1/fan_club/category_members/',
    '/media/sticker_tray_section/', '/direct_v2/ranked_recipients/',
    '/business/account/get_content_inspiration_medias/',
    '/accounts/get_controls_filtered_media/', '/address_book/get_ccu_setting/',
    '/api/v1/accounts/get_embeds_opt_out/', '/api/v1/accounts/last_password_change_timestamp/',
    '/business/account/get_suggested_hashtags/', '/map/search_null_state/',
    '/music/recent_searches/', '/notifications/get_notification_settings/',
    '/text_feed/ig_text_post_app_new_activity_feed_count/', '/users/get_message_settings_v2/',
}


def selector(signature):
    owner, tail = signature.split('->', 1)
    name, descriptor = tail.split('(', 1)
    return owner, name, '(' + descriptor


if __name__ == '__main__':
    operations = json.loads((DIRECTORY / 'operations.json').read_text())['operations']
    callers = {item['caller'] for operation in operations if operation['path'] in ROUTES and operation['method'] == 'GET' for item in operation['evidence'] if 'caller' in item}
    shared.SELECTORS.update(map(selector, callers))
    shared.SELECTORS.update({
        ('LX/03yq;', 'A00', '()Ljava/lang/String;'),
        ('LX/020p;', 'A0K', '(LX/04x5;Ljava/lang/String;)LX/02sG;'),
        ('LX/0o8B;', 'A01', '(LX/04x5;LX/05Dd;Ljava/lang/String;Ljava/lang/String;Z)LX/02sG;'),
        ('LX/0JTl;', 'A00', '(LX/06Sv;)Ljava/lang/String;'),
    })
    shared.SELECTORS.update({('LX/0GsX;', '<clinit>', '()V'), ('LX/0GsX;', 'toString', '()Ljava/lang/String;'), ('LX/0122;', 'A00', '(I)Ljava/lang/String;')})
    result = shared.collect(DIRECTORY.parents[1] / 'apks/base.apk')
    result.pop('rules')
    result['reviewed_routes'] = sorted(ROUTES)
    (DIRECTORY / 'read-repair-evidence.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'reviewed_routes': len(ROUTES), 'reviewed_methods': len(result['methods'])}))
