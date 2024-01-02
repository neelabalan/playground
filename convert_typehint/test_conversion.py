import unittest
from collections import namedtuple

from convert_typehint_ast import convert_typing_to_builtin

TestCase = namedtuple('TestCase', ['source_code', 'expected_code'])


class TestSamples:
    sample_1 = TestCase(
        source_code="""
from typing import List, Dict, Tuple

def example() -> List[Dict[str, Tuple[int, int]]]:
    return []
    """,
        expected_code="""
def example() -> list[dict[str, tuple[int, int]]]:
    return []
    """,
    )
    sample_2 = TestCase(
        source_code="""
def example() -> list[dict[str, tuple[int, int]]]:
    return []
        """,
        expected_code="""
def example() -> list[dict[str, tuple[int, int]]]:
    return []
        """,
    )


class TestTypingToBuiltinTransformer(unittest.TestCase):
    def test_convert_typing_to_builtin(self):
        for sample in [TestSamples.sample_1, TestSamples.sample_2]:
            new_code = convert_typing_to_builtin(sample.source_code)
            self.assertEqual(new_code.strip(), sample.expected_code.strip())


if __name__ == '__main__':
    unittest.main()
