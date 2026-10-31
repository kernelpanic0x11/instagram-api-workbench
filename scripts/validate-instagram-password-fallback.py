#!/usr/bin/env python3
"""Evaluate a narrow Instagram password-fallback model with synthetic data only.

This manually transcribed model is bound to reviewed static evidence. It does not
execute APK bytecode, load CryptoPubNative, serialize or dispatch a request, or
test server acceptance.
"""
import argparse
import base64
import contextlib
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACE = ROOT / 'apps/instagram/evidence/login-trace.json'
PINNED_APK_SHA256 = '4ca96b2b4023878010c5a1dd100662f5edb8b6f05c3b7a400c0c1ba251dfc52b'
PINNED_VERSION = '451.0.0.53.80'
SYNTHETIC_SENTINEL = 'IG_OFFLINE_SENTINEL_NOT_A_PASSWORD'
FIXED_TIMESTAMP = '1700000000'
INSTAGRAM_TAG = '#PWD_INSTAGRAM'
TRANSIENT_TAG = '#PWD_TRANSIENT'

TAG_METHOD = 'LX/0g5z;->A00(Ljava/lang/Integer;)Ljava/lang/String;'
FALLBACK_METHOD = 'LX/0hH7;->A00(Ljava/lang/String;Ljava/lang/String;LX/0hH7;)LX/0gYq;'
WRAPPER_CLASS_INIT = 'LX/0hHh;-><clinit>()V'
WRAPPER_INIT = 'LX/0hHh;-><init>(LX/05Dd;)V'
WRAPPER_METHOD = 'LX/0hHh;->A00(Ljava/lang/String;)Ljava/lang/String;'
WRAPPER_HELPER = 'LX/0227;->A0c(LX/05Dd;Ljava/lang/String;)Ljava/lang/String;'
KEY_STORE_METHOD = 'LX/0Gie;->A01()LX/0gTz;'
LOGIN_METHOD = ('LX/0537;->A06(LX/05Dd;Ljava/lang/String;Ljava/lang/String;'
                'Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;'
                'Ljava/lang/String;Ljava/lang/String;Ljava/util/List;I)LX/02sG;')
CRYPTO_CALL = ('Lcom/facebook/cryptopub/CryptoPubNative;->encrypt('
               'ILjava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B')

# Full instruction fingerprints make the model fail closed if the checked-in trace
# or a fresh extraction from the pinned APK no longer matches the reviewed methods.
EXPECTED_METHODS = {
    TAG_METHOD: ('classes22.dex', 4782448,
                 '32df940d069240f95a7e627485646484d61e0e5d31a3d7fb6892a7e8ab23b585'),
    FALLBACK_METHOD: ('classes22.dex', 4592764,
                      'b44cd72ddd4bd18e959e02b76a51b9813a692a54dd47c9d3c3ef79a70c29ff87'),
    WRAPPER_CLASS_INIT: ('classes22.dex', 2711124,
                         'd6c85e156ab6c9909ce734000da25618be2fe4277eb9b07cefc47a3c16ecf319'),
    WRAPPER_INIT: ('classes22.dex', 4521980,
                   'c0c2bc8908d886f52bba3634d4a3cdbdabc560f3cab8cdbadd06974296dd52cc'),
    WRAPPER_METHOD: ('classes22.dex', 4593012,
                     'c4174abeb743eb41260c1408142f0211f9ba4fcac39ea7ac94e346534d8ff519'),
    WRAPPER_HELPER: ('classes9.dex', 2382492,
                     'fa29c83a68736ba00cfbba8948c049d42a0e64bd2c565c176edf184845cd679a'),
    KEY_STORE_METHOD: ('classes7.dex', 7344712,
                       '9fa0972a743980b12a8adea782df741e852c780b1326a5956eeb0274dd550fdf'),
    LOGIN_METHOD: ('classes9.dex', 4607580,
                   '057e9f22aaac75db66aebdd6f3ff2cdbd78a02fc72741ee0aa141a64e5280aea'),
}

INTEGER_CLASS_INIT = 'LX/0009;-><clinit>()V'
INTEGER_CLASS_INIT_OFFSET = 3387892
INTEGER_CLASS_INIT_DIGEST = 'c3377dae2506fae6c8dc32cbe83fd4be99e6d497148bf4fcd94f45495862860b'


class EvidenceMismatch(ValueError):
    """Raised when trace evidence no longer matches the reviewed pinned client."""


class OfflineGuardViolation(RuntimeError):
    """Raised if the harness attempts networking or process execution."""


class SafeArgumentParser(argparse.ArgumentParser):
    """Reject invalid arguments without echoing a possibly secret value."""

    def error(self, _message):
        self.print_usage(sys.stderr)
        self.exit(2, 'error: invalid or unsupported arguments\n')


def instruction_digest(method):
    encoded = json.dumps(method['instructions'], sort_keys=True,
                         separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def _require(condition, message):
    if not condition:
        raise EvidenceMismatch(message)


def _method_map(trace):
    methods = trace.get('methods')
    _require(isinstance(methods, list), 'Trace methods are missing')
    result = {}
    for method in methods:
        signature = method.get('method')
        _require(isinstance(signature, str), 'Trace contains an invalid method record')
        _require(signature not in result, 'Trace contains a duplicate method record')
        result[signature] = method
    return result


def _strings(method):
    return [item['string'] for item in method['instructions'] if 'string' in item]


def _callees(method):
    return [item['callee'] for item in method['instructions'] if 'callee' in item]


def _fields(method):
    return [tuple(item['field']) for item in method['instructions'] if 'field' in item]


def _instruction_at(method, code_unit_offset):
    return next((item for item in method['instructions']
                 if item.get('code_unit_offset') == code_unit_offset), {})


def _const4_value(instruction):
    if instruction.get('opcode') != '0x12' or len(instruction.get('code_units', [])) != 1:
        return None
    value = (instruction['code_units'][0] >> 12) & 0xf
    return value - 16 if value >= 8 else value


def _validate_trace(trace):
    """Fail closed unless the trace matches the reviewed client and data-flow anchors."""
    _require(trace.get('app') == 'instagram', 'Trace app identity does not match')
    _require(trace.get('version') == PINNED_VERSION, 'Trace version does not match')
    _require(trace.get('apk_sha256') == PINNED_APK_SHA256, 'Trace APK digest does not match')
    _require(trace.get('status') ==
             'static evidence; no login request or server acceptance verified',
             'Trace scope statement is missing or changed')
    methods = _method_map(trace)

    for signature, (dex, offset, digest) in EXPECTED_METHODS.items():
        _require(signature in methods, 'Required reviewed method is missing')
        method = methods[signature]
        _require(method.get('dex') == dex, 'Reviewed method moved to an unexpected DEX')
        _require(method.get('code_item_byte_offset') == offset,
                 'Reviewed method offset changed')
        _require(instruction_digest(method) == digest,
                 'Reviewed method instructions changed')

    tag = methods[TAG_METHOD]
    fallback = methods[FALLBACK_METHOD]
    class_init = methods[WRAPPER_CLASS_INIT]
    wrapper_init = methods[WRAPPER_INIT]
    wrapper = methods[WRAPPER_METHOD]
    helper = methods[WRAPPER_HELPER]
    key_store = methods[KEY_STORE_METHOD]
    login = methods[LOGIN_METHOD]

    _require(INSTAGRAM_TAG in _strings(tag), 'Instagram password tag is missing')
    _require(('LX/0009;', 'A0N', 'Ljava/lang/Integer;') in _fields(class_init),
             'Wrapper tag selector initialization is missing')
    _require(_const4_value(_instruction_at(wrapper_init, 9)) == 4 and
             _instruction_at(wrapper_init, 10).get('field') == ['LX/0hH7;', 'A03', 'I'],
             'Version-4 constructor assignment is missing')
    _require(_const4_value(_instruction_at(wrapper_init, 12)) == 1 and
             _instruction_at(wrapper_init, 22).get('opcode') == '0x5c' and
             _instruction_at(wrapper_init, 22).get('field') == ['LX/0hH7;', 'A02', 'Z'],
             'Enabled fallback-mode constructor assignment is missing')
    _require(_instruction_at(fallback, 0).get('opcode') == '0x55' and
             _instruction_at(fallback, 0).get('field') == ['LX/0hH7;', 'A02', 'Z'],
             'Fallback-mode guard is missing')
    _require(CRYPTO_CALL in _callees(fallback),
             'Fallback helper no longer contains the default encryption path')
    _require([item['code_unit_offset'] for item in wrapper['instructions']
              if item.get('callee') == FALLBACK_METHOD] == [84, 115],
             'Missing-key and encryption-error fallback calls are not both present')
    _require(CRYPTO_CALL in _callees(wrapper), 'Native encryption call is missing')
    _require('%s:%s:%s:%s' in _strings(wrapper), 'Tagged envelope format is missing')
    _require(TRANSIENT_TAG in _strings(wrapper), 'Transient plaintext tag is missing')
    _require(WRAPPER_METHOD in _callees(helper), 'Password wrapper helper link is missing')
    _require({'ENCRYPTION_WITH_TAGGING', 'PLAINTEXT_WITH_TAGGING'}.issubset(_strings(key_store)),
             'Reviewed key-state branches are missing')
    _require('accounts/login/' in _strings(login), 'Login route is missing')
    _require('enc_password' in _strings(login), 'enc_password insertion is missing')
    _require(WRAPPER_HELPER in _callees(login), 'Login-to-wrapper call is missing')

    tag_proof = trace.get('local_apk_tag_constant_proof')
    if tag_proof is not None:
        _require(tag_proof == {
            'method': INTEGER_CLASS_INIT,
            'code_item_byte_offset': INTEGER_CLASS_INIT_OFFSET,
            'instruction_sha256': INTEGER_CLASS_INIT_DIGEST,
            'A0N_integer_value': 3,
        }, 'Pinned APK tag-constant proof changed')

    return {
        'apk_sha256': PINNED_APK_SHA256,
        'version': PINNED_VERSION,
        'reviewed_methods': len(EXPECTED_METHODS),
        'trace_methods': len(methods),
        'instruction_fingerprints_verified': True,
        'reviewed_data_flow_anchors_matched': True,
        'instagram_tag_constant_verified_from_apk': tag_proof is not None,
    }


def validate_trace(trace):
    """Normalize malformed or drifted evidence into one fail-closed exception."""
    try:
        return _validate_trace(trace)
    except EvidenceMismatch:
        raise
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as error:
        raise EvidenceMismatch('Trace evidence has an invalid structure') from error


def load_trace(path):
    try:
        trace = json.loads(path.read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceMismatch('Unable to read valid trace evidence') from error
    return trace


def _tag_constant_proof(path, helpers):
    """Bind A0N to integer 3 when the ignored pinned APK is available."""
    with zipfile.ZipFile(path) as archive:
        data = archive.read('classes.dex')
    dex = helpers.instruction_reader.Dex(data, 'classes.dex')
    matches = [(index, code) for index, code in dex.codes()
               if helpers.instruction_reader.sig(dex.methods[index]) == INTEGER_CLASS_INIT]
    _require(len(matches) == 1, 'Integer constant initializer is missing or ambiguous')
    _index, code = matches[0]
    _require(code == INTEGER_CLASS_INIT_OFFSET, 'Integer constant initializer moved')
    instructions, _bounds = dex.insns(code)
    records = [helpers.instruction_record(dex, instruction) for instruction in instructions]
    digest = hashlib.sha256(json.dumps(records, sort_keys=True,
                                       separators=(',', ':')).encode()).hexdigest()
    _require(digest == INTEGER_CLASS_INIT_DIGEST,
             'Integer constant initializer instructions changed')
    by_pc = {item['code_unit_offset']: item for item in records}
    _require(_const4_value(by_pc.get(25, {})) == 3 and
             by_pc.get(26, {}).get('callee') ==
             'Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;' and
             by_pc.get(30, {}).get('field') == ['LX/0009;', 'A0N', 'Ljava/lang/Integer;'],
             'Instagram tag selector no longer maps to integer 3')
    return {
        'method': INTEGER_CLASS_INIT,
        'code_item_byte_offset': INTEGER_CLASS_INIT_OFFSET,
        'instruction_sha256': INTEGER_CLASS_INIT_DIGEST,
        'A0N_integer_value': 3,
    }


def trace_pinned_apk(path):
    """Regenerate the selected trace in memory; never write or dispatch anything."""
    spec = importlib.util.spec_from_file_location(
        'instagram_login_trace', ROOT / 'scripts/trace-instagram-login.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        with contextlib.redirect_stdout(sys.stderr):
            result = module.trace(path)
        result['local_apk_tag_constant_proof'] = _tag_constant_proof(
            path, module.load_instruction_helpers())
        return result
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        raise EvidenceMismatch('Pinned APK verification or trace extraction failed') from error


def model_envelope(key_state, encryptor):
    """Narrow manual translation of reviewed branches using only the fixed sentinel."""
    if key_state not in {'missing', 'encryption-with-tagging', 'plaintext-with-tagging'}:
        raise ValueError('Unsupported synthetic key state')
    fallback_reason = None
    encryption_attempted = False
    plaintext_key_state_taken = False
    if key_state == 'missing':
        payload = SYNTHETIC_SENTINEL
        fallback_reason = 'missing-public-key'
    else:
        encryption_attempted = True
        try:
            encrypted = encryptor(SYNTHETIC_SENTINEL, FIXED_TIMESTAMP)
            if not isinstance(encrypted, bytes) or not encrypted:
                raise ValueError('Synthetic encryptor must return nonempty bytes')
            payload = base64.b64encode(encrypted).decode('ascii')
        except Exception:  # This intentionally models the reviewed catch-all branch.
            payload = SYNTHETIC_SENTINEL
            fallback_reason = 'encryption-exception'
    if key_state == 'plaintext-with-tagging':
        payload = SYNTHETIC_SENTINEL
        plaintext_key_state_taken = True
        tag = TRANSIENT_TAG
        version = 0
    else:
        tag = INSTAGRAM_TAG
        version = 0 if fallback_reason else 4
    envelope = f'{tag}:{version}:{FIXED_TIMESTAMP}:{payload}'
    return {
        'envelope': envelope,
        'tag': tag,
        'version': version,
        'fallback_taken': fallback_reason is not None,
        'fallback_reason': fallback_reason,
        'plaintext_key_state_taken': plaintext_key_state_taken,
        'raw_sentinel_path_taken': payload == SYNTHETIC_SENTINEL,
        'encryption_attempted': encryption_attempted,
    }


def pre_dispatch_field(envelope):
    """Model only the reviewed field insertion; no transport or dispatch exists here."""
    return {'enc_password': envelope}


def _forced_error(_sentinel, _timestamp):
    raise RuntimeError('forced synthetic encryption error')


def _synthetic_success(sentinel, timestamp):
    # This is an opaque control, not an implementation of Instagram encryption.
    return hashlib.sha256(('offline-control:' + timestamp + ':' + sentinel).encode()).digest()


def run_scenario(name, show_synthetic_field=False):
    if name == 'missing-key':
        modeled = model_envelope('missing', _forced_error)
    elif name == 'encrypt-error':
        modeled = model_envelope('encryption-with-tagging', _forced_error)
    elif name == 'plaintext-key-state':
        modeled = model_envelope('plaintext-with-tagging', _synthetic_success)
    elif name == 'success-control':
        modeled = model_envelope('encryption-with-tagging', _synthetic_success)
    else:
        raise ValueError('Unsupported validation scenario')
    fields = pre_dispatch_field(modeled.pop('envelope'))
    enc_password = fields['enc_password']
    result = {
        'scenario': name,
        **modeled,
        'sentinel_present_in_enc_password': SYNTHETIC_SENTINEL in enc_password,
        'sentinel_occurrences': enc_password.count(SYNTHETIC_SENTINEL),
        'enc_password_bytes': len(enc_password.encode()),
        'enc_password_sha256': hashlib.sha256(enc_password.encode()).hexdigest(),
        'enc_password_shape': (f'{modeled["tag"]}:{modeled["version"]}:'
                               '<fixed-timestamp>:<synthetic-or-opaque-payload>'),
    }
    if show_synthetic_field:
        result['pre_dispatch_fields'] = fields
    return result


def run_validation(trace, scenario='all', show_synthetic_field=False, source='checked-in-trace'):
    evidence = validate_trace(trace)
    names = ['missing-key', 'encrypt-error', 'plaintext-key-state',
             'success-control'] if scenario == 'all' else [scenario]
    scenarios = [run_scenario(name, show_synthetic_field) for name in names]
    by_name = {item['scenario']: item for item in scenarios}
    if 'missing-key' in by_name:
        _require(by_name['missing-key']['sentinel_occurrences'] == 1 and
                 by_name['missing-key']['version'] == 0,
                 'Missing-key model did not preserve the sentinel as expected')
    if 'encrypt-error' in by_name:
        _require(by_name['encrypt-error']['sentinel_occurrences'] == 1 and
                 by_name['encrypt-error']['version'] == 0,
                 'Encryption-error model did not preserve the sentinel as expected')
    if 'plaintext-key-state' in by_name:
        _require(by_name['plaintext-key-state']['sentinel_occurrences'] == 1 and
                 by_name['plaintext-key-state']['version'] == 0 and
                 by_name['plaintext-key-state']['tag'] == TRANSIENT_TAG,
                 'Plaintext key-state model did not preserve the sentinel as expected')
    if 'success-control' in by_name:
        _require(not by_name['success-control']['sentinel_present_in_enc_password'] and
                 by_name['success-control']['version'] == 4,
                 'Success control did not produce an opaque version-4 payload')
    return {
        'scope': ('Manually transcribed evidence-bound model; APK bytecode was not executed, '
                  'wire serialization was not reproduced, and server acceptance was not tested.'),
        'evidence_source': source,
        'evidence': evidence,
        'synthetic_input': {
            'built_in_only': True,
            'value_redacted_by_default': True,
            'timestamp_is_fixed_fixture': True,
        },
        'scenarios': scenarios,
        'network_requests': 0,
        'dispatch_available': False,
        'conclusion': ('The narrow model places the fixed synthetic sentinel in the '
                       'pre-dispatch enc_password field for the two failure paths and the '
                       'PLAINTEXT_WITH_TAGGING key-state path.'),
        'model_assumptions': ([] if evidence['instagram_tag_constant_verified_from_apk'] else [
            'The checked-in trace links A0N to the tag mapper but does not include the '
            'A0N integer initializer; use --apk to verify exact #PWD_INSTAGRAM selection.',
        ]),
        'limitations': [
            'The original Android method and CryptoPubNative JNI code were not executed.',
            'Runtime reachability, wire serialization, production dispatch, TLS processing, logging, and server acceptance remain untested.',
            'The success control is synthetic and is not compatible Instagram encryption.',
        ],
    }


def install_offline_audit_guard():
    """Fail closed if this process attempts networking or child-process dispatch."""
    state = {'blocked_attempts': 0}
    blocked_events = {
        'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.spawn',
        'os.exec', 'os.fork', 'os.forkpty', 'pty.spawn',
    }

    def guard(event, _arguments):
        if event.startswith('socket.') or event in blocked_events:
            state['blocked_attempts'] += 1
            raise OfflineGuardViolation('Offline harness blocked an external action')

    sys.addaudithook(guard)
    return state


def build_parser():
    parser = SafeArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--trace', type=Path, help='Static trace JSON; defaults to the checked-in pinned trace')
    source.add_argument('--apk', type=Path, help='Re-extract the trace in memory from the pinned base APK')
    parser.add_argument('--scenario', choices=['missing-key', 'encrypt-error',
                                               'plaintext-key-state', 'success-control', 'all'],
                        default='all')
    parser.add_argument('--show-synthetic-field', action='store_true',
                        help='Show the fixed sentinel in the modeled pre-dispatch field snapshot')
    parser.add_argument('--output', type=Path,
                        help='Optional new file for the sanitized JSON report; existing files are not overwritten')
    return parser


def main(argv=None):
    parser = build_parser()
    arguments = parser.parse_args(argv)
    guard = install_offline_audit_guard()
    try:
        if arguments.apk:
            trace = trace_pinned_apk(arguments.apk)
            source = 'pinned-apk-in-memory-trace'
        else:
            trace = load_trace(arguments.trace or DEFAULT_TRACE)
            source = 'checked-in-static-trace'
        report = run_validation(trace, arguments.scenario, arguments.show_synthetic_field, source)
        report['blocked_external_action_attempts'] = guard['blocked_attempts']
        rendered = json.dumps(report, indent=2, sort_keys=True) + '\n'
        if arguments.output:
            if arguments.output.exists():
                raise EvidenceMismatch('Refusing to overwrite an existing output file')
            try:
                arguments.output.write_text(rendered)
            except OSError as error:
                raise EvidenceMismatch('Unable to write the output report') from error
        sys.stdout.write(rendered)
        return 0
    except (EvidenceMismatch, OfflineGuardViolation) as error:
        parser.exit(2, f'error: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
