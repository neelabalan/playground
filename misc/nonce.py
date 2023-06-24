import hashlib
import itertools
from typing import Dict


def run(name: str) -> Dict:
    message = name + " {}"
    for counter in itertools.count(0):
        # print('counter - {}'.format(counter))
        digest = hashlib.sha256(message.format(counter).encode()).hexdigest()
        if digest[:5] == "00000":
            print(f"Found! \n sha256 - {digest} \n nonce - {counter}")
            return {"nonce": counter, "sha256digest": counter}


if __name__ == "__main__":
    run("neelabalan")
