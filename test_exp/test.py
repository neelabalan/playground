import inspect


def run_tests(module):
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if getattr(obj, '__test__', False):
            try:
                obj()
                print(f'{name} passed!')
            except AssertionError as ex:
                print(f'{name} failed: {ex}')


def test(func):
    func.__test__ = True
    return func
