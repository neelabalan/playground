from __future__ import annotations

from typing import List

import ray
from hypothesis import given, settings
from hypothesis import strategies as st
from typing_extensions import NoReturn

SAMPLES = 10_000

if not ray.is_initialized():
    ray.init(num_cpus=8)
# if ray.is_initialized():
    # ray.shutdown()


def fibonacci(n: int) -> List[int] | NoReturn:
    if n <= 0:
        raise ValueError("Number of terms in the Fibonacci sequence must be positive.")
    sequence = [0, 1]
    while len(sequence) < n:
        next_term = sequence[-1] + sequence[-2]
        sequence.append(next_term)
    return sequence


def collatz(n: int) -> List[int]:
    """Generate the Collatz sequence for a given positive integer"""
    sequence = [n]
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        sequence.append(n)
    return sequence


@ray.remote
@given(st.integers(min_value=1, max_value=1000))
@settings(deadline=None, max_examples=SAMPLES)
def test_collatz_conjecture_property(n):
    # Generate the Collatz sequence for the given positive integer n.
    # print(f'{n=}')
    sequence = collatz(n)
    # print(f'{sequence=}')
    # Verify that the sequence eventually reaches 1.
    assert isinstance(sequence, list)

@ray.remote
@given(st.integers(min_value=3, max_value=SAMPLES))
@settings(deadline=None, max_examples=SAMPLES)
def test_fibonacci_sequence_property(n: int):
    sequence = fibonacci(n)

    # print(f'{len(sequence)=}')
    # print(f'{n=}')
    assert len(sequence) == n
    for i in range(2, n):
        assert sequence[i] == sequence[i-1] + sequence[i-2]

if __name__ == "__main__":
    tests = [test_collatz_conjecture_property, test_fibonacci_sequence_property]
    test_results = ray.get([case.remote() for case in tests])
    # for test in tests:
    #     test()
