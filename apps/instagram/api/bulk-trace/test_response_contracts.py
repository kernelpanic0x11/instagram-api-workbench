"""Adversarial CFG tests: literals are not fields without a proven key reader."""
import importlib.util
from pathlib import Path
import unittest
from test_extract import Fixture

spec = importlib.util.spec_from_file_location('response_contracts', Path(__file__).with_name('trace-response-contracts.py'))
tracer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracer)

# Read a key from the input reader v7 into v1.
READ_KEY = [0x1071, 3, 7, 0x010c]
# Compare the key in v1 against literal v0.
COMPARE = [0x001a, 1, 0x206e, 4, 0x0001, 0x000e]


class ResponseContractTests(unittest.TestCase):
    def fields(self, words):
        fixture = Fixture(words)
        fixture.strings.append('synthetic_field')
        fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS])
        return tracer.dispatch_keys(fixture, 0, 16)[0]

    def test_field_key_comparison_is_recovered(self):
        self.assertEqual([field['name'] for field in self.fields(READ_KEY + COMPARE)], ['synthetic_field'])

    def test_non_input_reader_is_not_treated_as_root_fields(self):
        self.assertEqual(self.fields([0x1071, 3, 6, 0x010c] + COMPARE), [])

    def test_register_overwrite_discards_the_key(self):
        self.assertEqual(self.fields(READ_KEY + [0x1112] + COMPARE), [])

    def test_wide_register_overwrite_discards_adjacent_key(self):
        self.assertEqual(self.fields(READ_KEY + [0x4004] + COMPARE), [])

    def test_narrow_hash_bucket_arithmetic_preserves_adjacent_key(self):
        # Real generated parsers bucket hashCode() with and-int/lit8. Writing
        # v0 must not discard the previously decoded field key in v1.
        self.assertEqual([field['name'] for field in self.fields(
            READ_KEY + [0x00dd, 0x0f02] + COMPARE)], ['synthetic_field'])

    def test_unknown_wide_results_clobber_the_neighbor_but_narrow_results_do_not(self):
        # unary, binary, /2addr and array formats have different destination
        # layouts. Compare pairs with the same v0 destination and v1 key.
        for narrow, wide in [([0x207b], [0x207d]),
                             ([0x0090, 0x0302], [0x009b, 0x0302]),
                             ([0x20b0], [0x20bb]),
                             ([0x0044, 0x0302], [0x0045, 0x0302])]:
            with self.subTest(narrow=narrow, wide=wide):
                self.assertEqual(len(self.fields(READ_KEY + narrow + COMPARE)), 1)
                self.assertEqual(self.fields(READ_KEY + wide + COMPARE), [])

    def test_new_instance_overwrites_a_stale_key(self):
        self.assertEqual(self.fields(READ_KEY + [0x0122, 0] + COMPARE), [])

    def test_conflicting_control_flow_join_does_not_keep_one_paths_key(self):
        branch = [0x0338, 4, 0x0112, 0x0228, 0x0000]
        self.assertEqual(self.fields(READ_KEY + branch + COMPARE), [])

    def test_multiple_reader_sites_are_skipped_instead_of_flattening_nested_keys(self):
        self.assertEqual(self.fields(READ_KEY + READ_KEY + COMPARE), [])

    def test_verified_common_dispatcher_accepts_its_key_parameter(self):
        # The common dispatcher's third argument is v7, not v1.
        fixture = Fixture([0x001a, 1, 0x206e, 4, 0x0007, 0x000e])
        fixture.strings.append('synthetic_field')
        fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS])
        fixture.methods[0] = tracer.COMMON_DISPATCH
        fields, _ = tracer.dispatch_keys(fixture, 0, 16, delegated_key=True)
        self.assertEqual(fields[0]['name'], 'synthetic_field')
        self.assertEqual(fields[0]['evidence'][0]['key_source'], 'verified-delegated-key-parameter')

    def reader_fixture(self, branch=0x0238, reader=7, prefix=()):
        words = READ_KEY + [0x001a, 1, 0x206e, 4, 0x0001, 0x020a, branch, 6 + len(prefix)] + list(prefix) + [0x1071, 5, reader, 0x030a, 0x000e]
        fixture = Fixture(words)
        fixture.strings.append('synthetic_field')
        fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS, ('LX/0025;', 'A0H', '(LX/04s3;)Ljava/lang/Integer;')])
        return fixture

    def test_exclusive_true_prefix_records_reader_signature_without_wire_type(self):
        fixture = self.reader_fixture()
        field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
        self.assertEqual(field['client_reader_calls'][0]['callee'], 'LX/0025;->A0H(LX/04s3;)Ljava/lang/Integer;')
        self.assertEqual(field['client_reader_calls'][0]['return_descriptor'], 'Ljava/lang/Integer;')
        self.assertNotIn('wire_type', field)

    def test_false_branch_reader_is_not_assigned_to_matching_field(self):
        fixture = self.reader_fixture(branch=0x0239)
        self.assertEqual(tracer.dispatch_keys(fixture, 0, 16)[0][0]['client_reader_calls'], [])

    def test_different_or_overwritten_input_reader_does_not_get_bound(self):
        for fixture in [self.reader_fixture(reader=6), self.reader_fixture(prefix=[0x0712])]:
            self.assertEqual(tracer.dispatch_keys(fixture, 0, 16)[0][0]['client_reader_calls'], [])

    def test_token_advance_stops_value_context_but_current_token_peek_is_allowed(self):
        for method, expected in [('A1N', False), ('A1d', True)]:
            fixture=self.reader_fixture(prefix=[0x106e,6,7,0x030c])
            fixture.methods.append(('LX/04s3;',method,'()LX/01yl;'))
            field=tracer.dispatch_keys(fixture,0,16)[0][0]
            self.assertEqual(bool(field['client_reader_calls']),expected)

    def test_join_into_matched_prefix_stops_reader_inference(self):
        fixture = self.reader_fixture()
        instructions = {item[0]: item for item in fixture.insns(16)[0]}
        result = tracer.matched_reader_call(fixture, instructions[6], {12:{7:('reader',)}}, instructions, {12:{10,99}})
        self.assertIsNone(result)

    def null_guard_fixture(self, token='A0G', reader=7, branch=0x4332):
        # Peek current token into v3, load VALUE_NULL into v4, and skip the
        # matched reader call only when currentToken == VALUE_NULL.
        prefix = [0x106e, 6, reader, 0x030c, 0x0462, 2, branch, 6]
        fixture = self.reader_fixture(prefix=prefix)
        fixture.methods.append(('LX/04s3;', 'A1d', '()LX/01yl;'))
        fixture.fields.append(('LX/01yl;', token, 'LX/01yl;'))
        return fixture

    def test_reviewed_current_token_null_guard_keeps_conditional_reader_evidence(self):
        fixture = self.null_guard_fixture()
        field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
        call = field['client_reader_calls'][0]
        self.assertEqual(call['client_token_guards'][0]['condition'], 'current token is not VALUE_NULL')
        self.assertEqual(call['code_unit_offset'], 20)
        self.assertNotIn('nullable', field)
        self.assertNotIn('wire_type', field)

    def test_unreviewed_token_guards_or_null_branch_reads_are_not_bound(self):
        for fixture in (self.null_guard_fixture(token='A0D'),
                        self.null_guard_fixture(reader=6),
                        self.null_guard_fixture(branch=0x4333)):
            self.assertEqual(tracer.dispatch_keys(fixture, 0, 16)[0][0]['client_reader_calls'], [])

    def test_key_name_survives_reader_advance_but_direct_value_binding_does_not(self):
        words = READ_KEY + [0x106e, 6, 7] + [0x001a, 1, 0x206e, 4, 0x0001,
                0x020a, 0x0238, 6, 0x1071, 5, 7, 0x030a, 0x000e]
        fixture = Fixture(words)
        fixture.strings.append('synthetic_field')
        fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS,
            ('LX/0025;', 'A0H', '(LX/04s3;)Ljava/lang/Integer;'),
            ('LX/04s3;', 'A1N', '()LX/01yl;')])
        field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
        self.assertEqual(field['name'], 'synthetic_field')
        self.assertEqual(field['client_reader_calls'], [])

    def test_token_snapshot_before_reading_new_key_cannot_guard_its_value(self):
        words = [0x106e, 6, 7, 0x030c] + READ_KEY + [0x001a, 1, 0x206e, 4, 0x0001,
                 0x020a, 0x0238, 10, 0x0462, 2, 0x4332, 6, 0x1071, 5, 7, 0x050a, 0x000e]
        fixture = Fixture(words)
        fixture.strings.append('synthetic_field')
        fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS,
            ('LX/0025;', 'A0H', '(LX/04s3;)Ljava/lang/Integer;'),
            ('LX/04s3;', 'A1d', '()LX/01yl;')])
        fixture.fields.append(('LX/01yl;', 'A0G', 'LX/01yl;'))
        field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
        self.assertEqual(field['name'], 'synthetic_field')
        self.assertEqual(field['client_reader_calls'], [])

    def test_reader_identity_cast_is_skipped_before_the_first_consuming_call(self):
        fixture = self.reader_fixture(reader=6, prefix=[0x1071, 6, 7, 0x060c])
        fixture.methods.append(next(iter(tracer.READER_IDENTITY_HELPERS)))
        call = tracer.dispatch_keys(fixture, 0, 16)[0][0]['client_reader_calls'][0]
        self.assertEqual(call['callee'], 'LX/0025;->A0H(LX/04s3;)Ljava/lang/Integer;')
        self.assertEqual(call['code_unit_offset'], 16)

    def test_forwarding_parser_requires_an_untouched_input_reader(self):
        def fixture(prefix=(), reader=7):
            words = list(prefix) + [0x0262, 2, 0x206e, 3, (reader << 4) | 2, 0x000c, 0x0011]
            value = Fixture(words)
            value.fields.append(('LDelegate;', 'INSTANCE', 'LDelegate;'))
            value.methods.append(('LX/05Bj;', 'parseFromJsonParser', '(LX/04s3;)Ljava/lang/Object;'))
            return value
        value = fixture()
        self.assertEqual(tracer.parser_delegates(value, 0, 16)[0]['type'], 'LDelegate;')
        self.assertEqual(tracer.parser_delegates(fixture(reader=6), 0, 16), [])
        self.assertEqual(tracer.parser_delegates(fixture([0x1071, 2, 7]), 0, 16), [])
        self.assertEqual(tracer.parser_delegates(fixture([0x0138, 2]), 0, 16), [])


class DecodedResponseKeyTests(unittest.TestCase):
    def fixture(self, prefix=()):
        words=READ_KEY+[0x0213,0x140]+list(prefix)+[0x1071,5,2,0x000c,0x206e,4,0x0001,0x000e]
        value=Fixture(words)
        value.methods.extend([tracer.FIELD_READER,tracer.STRING_EQUALS,('LX/0021;','A00','(I)Ljava/lang/String;')])
        return value

    def test_decoded_key_keeps_cross_dex_literal_proof_without_false_local_string_index(self):
        fixture=self.fixture();decoder=fixture.methods[5]
        fields,_=tracer.dispatch_keys(fixture,0,16,literal_decoders={decoder:{0x140:{'value':'media_infos','proof':{'dex':'decoder.dex','string_index':42}}}})
        self.assertEqual(fields[0]['name'],'media_infos')
        self.assertEqual(fields[0]['evidence'][0]['literal_decoder']['dex'],'decoder.dex')
        self.assertNotIn('string_index',fields[0]['evidence'][0])
        self.assertNotIn('wire_type',fields[0])

    def test_unresolved_or_overwritten_decoder_index_never_becomes_a_response_field(self):
        for prefix in [(),(0x0212,)]:
            fixture=self.fixture(prefix);decoder=fixture.methods[5]
            mapping={} if not prefix else {0x140:{'value':'media_infos','proof':{}}}
            self.assertEqual(tracer.dispatch_keys(fixture,0,16,literal_decoders={decoder:mapping})[0],[])


class ReviewedDispatchHelperTests(unittest.TestCase):
    def fixture(self, words, helper):
        value = Fixture(words)
        value.strings.append('synthetic_field')
        value.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS, helper])
        return value

    def test_shared_equality_helpers_require_a_key_and_literal_in_reviewed_positions(self):
        for name, arguments in [('A0E', 0x1067), ('A0F', 0x1067), ('A0I', 0x6107)]:
            helper = next(method for method in tracer.FIELD_DISPATCH_HELPERS if method[1] == name)
            words = READ_KEY + [0x001a, 1, 0x4071, 5, arguments, 0x000e]
            fixture = self.fixture(words, helper)
            field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
            self.assertEqual(field['name'], 'synthetic_field')
            self.assertEqual(field['evidence'][0]['comparison_helper'], tracer.sig(helper))
            self.assertEqual(field['client_reader_calls'][0]['scope'], 'reviewed-helper-equality-true-value-read')
            self.assertNotIn('wire_type', field)
            for overwrite in ([0x0112], [0x0012], [0x0712]):
                fixture = self.fixture(READ_KEY + [0x001a, 1] + overwrite + [0x4071, 5, arguments, 0x000e], helper)
                self.assertEqual(tracer.dispatch_keys(fixture, 0, 16)[0], [])

    def test_internal_key_reader_helper_recovers_only_its_root_reader_literal(self):
        helper = next(method for method in tracer.FIELD_DISPATCH_HELPERS if method[1] == 'A0c')
        words = [0x001a, 1, 0x4071, 5, 0x0567, 0x000e]
        field = tracer.dispatch_keys(self.fixture(words, helper), 0, 16)[0][0]
        self.assertEqual(field['name'], 'synthetic_field')
        self.assertEqual(field['evidence'][0]['key_source'], 'input-reader-key-read-inside-reviewed-helper')
        wrong_reader = [0x001a, 1, 0x4071, 5, 0x0566, 0x000e]
        self.assertEqual(tracer.dispatch_keys(self.fixture(wrong_reader, helper), 0, 16)[0], [])
        self.assertEqual(tracer.dispatch_keys(self.fixture(READ_KEY + words, helper), 0, 16)[0], [])

    def test_five_argument_helper_does_not_confuse_model_or_prior_value_with_key(self):
        helper = next(method for method in tracer.FIELD_DISPATCH_HELPERS if method[1] == 'A0m')
        words = READ_KEY + [0x001a, 1, 0x5671, 5, 0x1057, 0x000e]
        fixture = self.fixture(words, helper)
        self.assertEqual(tracer.dispatch_keys(fixture, 0, 16)[0][0]['name'], 'synthetic_field')
        # Swap the genuine key with the previous string value (last argument).
        words = READ_KEY + [0x001a, 1, 0x5171, 5, 0x6057, 0x000e]
        self.assertEqual(tracer.dispatch_keys(self.fixture(words, helper), 0, 16)[0], [])

    def test_literal_predicate_helper_has_no_false_caller_string_index(self):
        helper = next(method for method in tracer.FIELD_DISPATCH_HELPERS if method[1] == 'A1b')
        words = READ_KEY + [0x1071, 5, 1, 0x020a, 0x0238, 6, 0x1071, 6, 7, 0x030a, 0x000e]
        fixture = self.fixture(words, helper)
        fixture.methods.append(('LX/0025;', 'A0H', '(LX/04s3;)Ljava/lang/Integer;'))
        field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
        self.assertEqual(field['name'], 'items')
        self.assertNotIn('string_index', field['evidence'][0])
        self.assertEqual(field['evidence'][0]['literal_helper'], tracer.sig(helper))
        self.assertEqual(len(field['client_reader_calls']), 1)

    def test_literal_predicate_does_not_bind_a_value_after_reader_advance(self):
        helper = next(method for method in tracer.FIELD_DISPATCH_HELPERS if method[1] == 'A1b')
        words = READ_KEY + [0x106e, 6, 7, 0x1071, 5, 1, 0x020a, 0x0238, 6,
                            0x1071, 7, 7, 0x030a, 0x000e]
        fixture = self.fixture(words, helper)
        fixture.methods.extend([('LX/04s3;', 'A1N', '()LX/01yl;'),
                                ('LX/0025;', 'A0H', '(LX/04s3;)Ljava/lang/Integer;')])
        field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
        self.assertEqual(field['name'], 'items')
        self.assertEqual(field['client_reader_calls'], [])

    def test_shared_equality_keeps_a_stale_key_name_without_its_value_binding(self):
        helper = next(method for method in tracer.FIELD_DISPATCH_HELPERS if method[1] == 'A0E')
        words = READ_KEY + [0x106e, 6, 7, 0x001a, 1, 0x4071, 5, 0x1067, 0x000e]
        fixture = self.fixture(words, helper)
        fixture.methods.append(('LX/04s3;', 'A1N', '()LX/01yl;'))
        field = tracer.dispatch_keys(fixture, 0, 16)[0][0]
        self.assertEqual(field['name'], 'synthetic_field')
        self.assertEqual(field['client_reader_calls'], [])

    def test_reviewed_cast_helper_preserves_only_the_identical_input_reader(self):
        helper = next(iter(tracer.READER_IDENTITY_HELPERS))
        for source, expected in [(7, True), (5, False)]:
            words = [0x1071, 5, source, 0x060c, 0x1071, 3, 6, 0x010c] + COMPARE
            fixture = self.fixture(words, helper)
            self.assertEqual(bool(tracer.dispatch_keys(fixture, 0, 16)[0]), expected)
        fixture = self.fixture([0x1071, 5, 7, 0x060c, 0x1071, 3, 6, 0x010c] + COMPARE,
                               ('LUnknown;', 'cast', helper[2]))
        self.assertEqual(tracer.dispatch_keys(fixture, 0, 16)[0], [])


class DelegatedRootKeyTests(unittest.TestCase):
    def dispatcher(self, reader_position=0):
        return next(method for method, mapping in tracer.KEY_DISPATCHERS.items()
                    if method != tracer.COMMON_DISPATCH and mapping['reader_argument'] == reader_position)

    def test_reviewed_dispatcher_entry_uses_its_actual_reader_parameter_position(self):
        helper = self.dispatcher(reader_position=1)
        # Three arguments occupy v5(model), v6(reader), v7(key).
        words = [0x001a, 1, 0x206e, 4, 0x0007, 0x020a, 0x0238, 6,
                 0x1071, 5, 6, 0x030a, 0x000e]
        fixture = Fixture(words)
        fixture.strings.append('synthetic_field')
        fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS,
                                ('LX/0025;', 'A0H', '(LX/04s3;)Ljava/lang/Integer;')])
        fixture.methods[0] = helper
        field = tracer.dispatch_keys(fixture, 0, 16, delegated_key=True)[0][0]
        self.assertEqual(field['name'], 'synthetic_field')
        self.assertEqual(len(field['client_reader_calls']), 1)

    def test_unknown_dispatcher_cannot_claim_predecoded_key_parameters(self):
        fixture = Fixture([0x000e])
        with self.assertRaisesRegex(ValueError, 'reviewed field dispatchers'):
            tracer.dispatch_keys(fixture, 0, 16, delegated_key=True)

    def test_forwarding_model_requires_both_the_original_reader_and_decoded_key(self):
        helper = self.dispatcher()
        child = {'name': 'child_field', 'evidence': [{'caller': tracer.sig(helper)}], 'client_reader_calls': []}
        for arguments, expected in [(0x0157, True), (0x0156, False), (0x0257, False)]:
            fixture = Fixture(READ_KEY + [0x3071, 5, arguments, 0x000e])
            fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS, helper])
            fields, _ = tracer.dispatch_keys(fixture, 0, 16, delegated_fields={helper: [child]})
            self.assertEqual(bool(fields), expected)
            if expected:
                self.assertEqual(fields[0]['evidence'][0]['key_delegation']['field_reader_code_unit_offset'], 0)
                self.assertEqual(fields[0]['evidence'][0]['key_delegation']['callee'], tracer.sig(helper))

    def test_reader_advance_between_key_and_delegate_discards_value_context(self):
        helper = self.dispatcher()
        fixture = Fixture(READ_KEY + [0x106e, 6, 7, 0x3071, 5, 0x0157, 0x000e])
        fixture.methods.extend([tracer.FIELD_READER, tracer.STRING_EQUALS, helper,
                                ('LX/04s3;', 'A1N', '()LX/01yl;')])
        child = {'name': 'child_field', 'evidence': [{}], 'client_reader_calls': []}
        self.assertEqual(tracer.dispatch_keys(fixture, 0, 16, delegated_fields={helper: [child]})[0], [])

if __name__ == '__main__':
    unittest.main()
