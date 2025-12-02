import argparse
import dataclasses
import sys
import tracemalloc


class RegularClass:
    def __init__(self, attr1: int, attr2: str, attr3: float, attr4: bool, attr5: list):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3
        self.attr4 = attr4
        self.attr5 = attr5


class RegularClassWithSlots:
    __slots__ = ('attr1', 'attr2', 'attr3', 'attr4', 'attr5')

    def __init__(self, attr1: int, attr2: str, attr3: float, attr4: bool, attr5: list):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3
        self.attr4 = attr4
        self.attr5 = attr5


@dataclasses.dataclass
class DataClass:
    attr1: int
    attr2: str
    attr3: float
    attr4: bool
    attr5: list


@dataclasses.dataclass(frozen=True)
class DataClassFrozen:
    attr1: int
    attr2: str
    attr3: float
    attr4: bool
    attr5: list


@dataclasses.dataclass(slots=True)
class DataClassWithSlots:
    attr1: int
    attr2: str
    attr3: float
    attr4: bool
    attr5: list


@dataclasses.dataclass(frozen=True, slots=True)
class DataClassFrozenWithSlots:
    attr1: int
    attr2: str
    attr3: float
    attr4: bool
    attr5: list


def create_instances(cls: type, count: int) -> list:
    return [cls(i, f'string_{i}', float(i), i % 2 == 0, [i]) for i in range(count)]


def calculate_total_size(instances: list) -> int:
    total = 0
    for obj in instances:
        total += sys.getsizeof(obj)
        if hasattr(obj, '__dict__'):
            total += sys.getsizeof(obj.__dict__)
    return total


def measure_memory_with_tracemalloc(cls: type, count: int) -> int:
    tracemalloc.start()
    instances = create_instances(cls, count)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    _ = instances
    return current


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=10000)
    args = parser.parse_args()
    instance_count = args.count

    classes = [
        ('regular class', RegularClass),
        ('regular class with slots', RegularClassWithSlots),
        ('dataclass', DataClass),
        ('dataclass frozen', DataClassFrozen),
        ('dataclass with slots', DataClassWithSlots),
        ('dataclass frozen with slots', DataClassFrozenWithSlots),
    ]

    print(f'instance count: {instance_count}')
    print()
    print('sys.getsizeof measurements:')
    sizes = {}
    for name, cls in classes:
        instances = create_instances(cls, instance_count)
        size = calculate_total_size(instances)
        sizes[name] = size
        print(f'{name}: {size} bytes')

    print()
    print('tracemalloc measurements:')
    tracemalloc_sizes = {}
    for name, cls in classes:
        mem = measure_memory_with_tracemalloc(cls, instance_count)
        tracemalloc_sizes[name] = mem
        print(f'{name}: {mem} bytes')


if __name__ == '__main__':
    main()
