import functools

class Car:
    pass

class Bike:
    pass


@functools.singledispatch
def dispatch_on_type(x):
    # some default logic
    print("I am the default call")


@dispatch_on_type.register(Car)
def _(x):
    print("This is car type")

@dispatch_on_type.register(Bike)
def _(x):
    print("This is bike type")


@dispatch_on_type.register(int)
def _(x):
    print("This is int type")


dispatch_on_type(Car())
dispatch_on_type(Bike())
dispatch_on_type(1)