"""Check token-enum provenance with synthetic DEX instructions."""
import importlib.util
from pathlib import Path
import unittest
from test_extract import Fixture

spec = importlib.util.spec_from_file_location('shared_contracts', Path(__file__).with_name('trace-shared-contracts.py'))
tracer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracer)


class SharedContractTests(unittest.TestCase):
    def fixture(self, clobber=()):
        words = [0x031a, 1, 0x0022, 0] + list(clobber) + [0x5470, 3, 0x3210, 0x0069, 2, 0x000e]
        fixture = Fixture(words)
        fixture.strings.append('START_OBJECT')
        fixture.fields.append(('LX/01yl;', 'A0D', 'LX/01yl;'))
        fixture.methods.append(('LX/01yl;', '<init>', '(IILjava/lang/String;Ljava/lang/String;)V'))
        return fixture

    def test_enum_name_is_bound_to_the_constructed_object_and_field(self):
        self.assertEqual(tracer.token_enum(self.fixture(), 16)['A0D']['name'], 'START_OBJECT')

    def test_overwritten_name_does_not_reuse_a_stale_literal(self):
        self.assertEqual(tracer.token_enum(self.fixture([0x0312]), 16), {})

    def test_other_constructor_does_not_create_an_enum_mapping(self):
        fixture = self.fixture()
        fixture.methods[3] = ('LUnknown;', '<init>', fixture.methods[3][2])
        self.assertEqual(tracer.token_enum(fixture, 16), {})


if __name__ == '__main__':
    unittest.main()
