from random import randint, choice
import math

def superincreasing_knapsack(count):
	knapsack = [randint(1, 20)]
	while len(knapsack) < count:
		randnum = randint(1, sum(knapsack)+randint(1, 100))
		if sum(knapsack) < randnum:
			knapsack.append(randnum)
	return knapsack


def coprimes(knapsack):
	modulus = randint(sum(knapsack), sum(knapsack) + 1000)
	multiplier = find_coprime(modulus)
	return modulus, multiplier 


def find_coprime(n):
	coprimes = filter(
		lambda num: math.gcd(n, num) == 1, list(range(n))
	)
	return choice(list(coprimes))


def convert_to_general_knapsack(superincreasing_knapsack, modulus, multiplier):
	return [(num*multiplier)%modulus for num in superincreasing_knapsack]


def bin_conversion(num: int):
    return [int(i) for i in list('{0:08b}'.format(num))]


def encrypt(public_key: list, text: str):
    cipher_text = list()
	# convert every character to integer 
    for char in text:
        binary_form = bin_conversion(ord(char))
        cipher_text.append(sum([i*j for i, j in zip(public_key, binary_form)]))
    return cipher_text


def solve_knapsack(capacity, weights):
    seq = list()
    for item in reversed(weights):
        if capacity >= item:
            seq.append(1)
            capacity -= item
        else:
            seq.append(0)
    return list(reversed(seq)) if capacity == 0 else None

# https://stackoverflow.com/a/64391815/4873716
def binary_seq_to_integer(binary_seq: list) -> int:
  number = 0
  for bit in binary_seq:
    number = (2 * number) + bit
  return number

def decrypt(cipher_text: list, priv_key: list, modulus: int, multiplier: int):
    # python 3.8+
    mod_inverse = pow(multiplier, -1, modulus)
    plain_text = list()
    for val in cipher_text:
        coded_val = (val*mod_inverse)%modulus
        binary_seq = solve_knapsack(coded_val, priv_key)
        plain_text.append(
			chr(binary_seq_to_integer(binary_seq))
		)
        print(plain_text)

    return ''.join(plain_text)

