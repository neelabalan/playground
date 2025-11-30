import unittest

from merkle_hellman_crypto import *


class MerkleHellmanCrypto(unittest.TestCase):
    def test(self):
        message = 'the secret'
        priv_key = superincreasing_knapsack(8)  # 8 bit
        mod, mul = coprimes(priv_key)
        pub_key = convert_to_general_knapsack(priv_key, mod, mul)
        cipher_text = encrypt(pub_key, message)
        print(
            """
            message = {}
            private key = {}
            public_key = {}
            modulus = {}
            multiplier = {}
            cipher_text = {}
            """.format(message, priv_key, pub_key, mod, mul, cipher_text)
        )
        decrypted_msg = decrypt(cipher_text, priv_key, mod, mul)
        self.assertEqual(message, decrypted_msg)
        # print('decrypted message = {}'.format(decrypted_msg))
