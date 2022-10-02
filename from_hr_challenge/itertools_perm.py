"""
Input

HACK 2

Output

AC
AH
AK
CA
CH
CK
HA
HC
HK
KA
KC
KH
"""
from itertools import permutations as perm

def run():
    chars, k = input().split(' ')
    print(
        '\n'.join([
            ''.join(char_tup) for char_tup in perm(sorted(chars), int(k))
        ])
    )

if __name__ == '__main__':
    run()