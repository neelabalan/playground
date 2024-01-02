import datetime as dt
import itertools
import secrets
from io import BufferedReader

import click

KEY_LENGTH = 16


def byte_xor(key: bytes, text: bytes) -> bytes:
    """XOR operation on bytes"""
    return bytes([x ^ y for x, y in zip(itertools.cycle(key), text)])


def encrypt(source: BufferedReader, output: BufferedReader):
    output.write(byte_xor(key=generate_random_key(), text=source.read()))


def decrypt(encryptedfile: BufferedReader, output: BufferedReader, keyfile: BufferedReader):
    filecontent = encryptedfile.read()
    key = keyfile.read()
    output.write(byte_xor(key, filecontent))


def generate_random_key() -> bytes:
    key = secrets.token_bytes(KEY_LENGTH)
    filename = '-'.join(['key', dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')]) + '.txt'
    with open(filename, 'wb') as file:
        file.write(key)
        print('key stored as: ', filename)
    return key


@click.command()
@click.option('--key', type=click.File('rb'))
@click.option('--filein', required=True, type=click.File('rb'))
@click.option('--output', required=True, type=click.File('wb'))
def run(key, filein, output):
    """
    if the key is not provided as input then it is encryption process takes place
    """
    if key:
        decrypt(encryptedfile=filein, output=output, keyfile=key)
    else:
        encrypt(source=filein, output=output)


if __name__ == '__main__':
    run()
