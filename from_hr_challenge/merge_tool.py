"""
Input

STDIN       Function
-----       --------
AABCAAADA   s = 'AABCAAADA'
3           k = 3

Output

AB
CA
AD

### Explanation

Split s into n/k = 9/3 equal parts of length k = 3.

1. AAB -> AB
2. CAA -> CA
3. ADA -> AD

"""
import textwrap  # for splitting the string in equal parts
from collections import Counter


def merge_the_tools(string, k):
    splits = textwrap.wrap(string, k)
    split_freq = [Counter(strval) for strval in splits]
    print("\n".join(["".join(freq_map.keys()) for freq_map in split_freq]))
