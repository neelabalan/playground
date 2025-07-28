"""
`venv/bin/python -m pytest --csv tests.csv`

`pytest --html=report.html --self-contained-html`

`pytest -s --hypothesis-verbosity=verbose`
"""

from hypothesis import given
from hypothesis import strategies as st
from source_file import add
from source_file import divide
from source_file import multiply


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False, min_value=1e-6),
)
def test_add_property(a, b):
    assert add(a, b) == a + b


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False, min_value=1e-6),
)
def test_multiply_property(a, b):
    assert multiply(a, b) == a * b


@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False, min_value=1e-6),
)
def test_divide_property(a, b):
    if b != 0:
        assert divide(a, b) == a / b
