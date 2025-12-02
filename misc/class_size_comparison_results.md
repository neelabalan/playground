# Class Size Comparison Results

Comparison of memory usage between regular class, dataclass, and their variants with `__slots__` and `frozen=True`.

## Test Setup

- OS: macOS 14.8.1 (arm64)
- Python versions: 3.11, 3.13
- Instance counts tested: 10,000 / 30,000 / 50,000
- Attributes per instance: 5 (`int`, `str`, `float`, `bool`, `list`)

### Class Types Tested

| Class Type                  | Description                                               |
| --------------------------- | --------------------------------------------------------- |
| Regular Class               | Standard Python class with `__init__`                     |
| Regular Class with Slots    | Class with `__slots__` defined (no `__dict__`)            |
| Dataclass                   | `@dataclass` decorator                                    |
| Dataclass Frozen            | `@dataclass(frozen=True)` - immutable instances           |
| Dataclass with Slots        | `@dataclass(slots=True)` - no `__dict__`                  |
| Dataclass Frozen with Slots | `@dataclass(frozen=True, slots=True)` - immutable + slots |

### Measurement Methods

- sys.getsizeof: measures object size + `__dict__` size (if present)
- tracemalloc: tracks actual memory allocations by Python memory allocator

## Results

### sys.getsizeof measurements (bytes)

| Class Type                  | 10k (3.11) | 10k (3.13) | 30k (3.11) | 30k (3.13) | 50k (3.11) | 50k (3.13) |
| --------------------------- | ---------- | ---------- | ---------- | ---------- | ---------- | ---------- |
| Regular Class               | 1,680,000  | 1,600,000  | 5,040,000  | 4,800,000  | 8,400,000  | 8,000,000  |
| Regular Class with Slots    | 720,000    | 720,000    | 2,160,000  | 2,160,000  | 3,600,000  | 3,600,000  |
| Dataclass                   | 1,680,000  | 1,600,000  | 5,040,000  | 4,800,000  | 8,400,000  | 8,000,000  |
| Dataclass Frozen            | 1,680,000  | 1,600,000  | 5,040,000  | 4,800,000  | 8,400,000  | 8,000,000  |
| Dataclass with Slots        | 720,000    | 720,000    | 2,160,000  | 2,160,000  | 3,600,000  | 3,600,000  |
| Dataclass Frozen with Slots | 720,000    | 720,000    | 2,160,000  | 2,160,000  | 3,600,000  | 3,600,000  |

### tracemalloc measurements (bytes)

| Class Type                  | 10k (3.11) | 10k (3.13) | 30k (3.11) | 30k (3.13) | 50k (3.11) | 50k (3.13) |
| --------------------------- | ---------- | ---------- | ---------- | ---------- | ---------- | ---------- |
| Regular Class               | 2,988,962  | 2,908,962  | 9,010,274  | 8,770,274  | 15,068,162 | 14,668,162 |
| Regular Class with Slots    | 2,589,042  | 2,508,962  | 7,810,354  | 7,570,274  | 13,068,242 | 12,668,162 |
| Dataclass                   | 2,988,962  | 2,908,962  | 9,010,274  | 8,770,274  | 15,068,162 | 14,668,162 |
| Dataclass Frozen            | 2,989,026  | 2,908,962  | 9,010,474  | 8,770,338  | 15,068,282 | 14,668,282 |
| Dataclass with Slots        | 2,588,962  | 2,508,962  | 7,810,274  | 7,570,274  | 13,068,162 | 12,668,162 |
| Dataclass Frozen with Slots | 2,589,082  | 2,509,082  | 7,810,338  | 7,570,394  | 13,068,282 | 12,668,282 |

## Observations

1. `__slots__` provides significant memory savings (~57% reduction in sys.getsizeof, ~13% in tracemalloc)
2. Regular class and dataclass have identical memory footprint - dataclass is just syntactic sugar
3. `frozen=True` has negligible memory overhead (< 200 bytes difference across all tests)
4. Python 3.13 is slightly more memory efficient than 3.11 for non-slotted classes (~5% improvement)
5. Slotted classes have identical size across Python 3.11 and 3.13
6. Memory scales linearly with instance count as expected
