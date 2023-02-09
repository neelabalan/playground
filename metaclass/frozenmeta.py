class FrozenMeta(type):
    def __new__(cls, name, bases, arg):
        inst = super().__new__(cls, name, bases, {"_FrozenMeta__frozen": False, **arg})
        inst.__frozen = True
        return inst

    def __setattr__(self, key, value):
        if self.__frozen:
            raise AttributeError("Cannot set/change the attributes")
        super().__setattr__(key, value)

    def __str__(cls):
        pass


class A(metaclass=FrozenMeta):
    a = 1
    b = 2
