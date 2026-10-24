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


if __name__ == '__main__':
    unittest.main()
