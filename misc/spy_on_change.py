# https://nedbatchelder.com/blog/202206/adding_a_dunder_to_an_object.html


class SomeObject:
    ...


class Nothing:
    """Just to get a nice repr for Nothing."""

    def __repr__(self):
        return '<Nothing>'


obj = SomeObject()
obj.attr = 'first'
print(obj.attr)


def spy_on_changes(obj):
    """Tweak an object to show attributes changing."""

    class Wrapper(obj.__class__):
        def __setattr__(self, name, value):
            old = getattr(self, name, Nothing())
            print(f'Spy: {name}: {old!r} -> {value!r}')
            return super().__setattr__(name, value)

    obj.__class__ = Wrapper


spy_on_changes(obj)
obj.attr = 'second'
# Spy: attr: 'first' -> 'second'

print(obj.attr)
# 'second'

obj.another = 'foo'
# Spy: another: <Nothing> -> 'foo'
