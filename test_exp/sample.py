import sys
  from test import test, run_tests

@test
def example_test():
    assert 1 + 1 == 2

@test
def another_example_test():
    assert [1, 2, 3] == [1, 2, 3]

def not_a_test():
    assert True == False

run_tests(sys.modules[__name__])
  