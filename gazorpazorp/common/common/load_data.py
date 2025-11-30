import json
import pathlib
from typing import Dict
from typing import List


def load_characters() -> List[Dict]:
    # get current path using pathlib
    current_path = pathlib.Path(__file__).resolve().parent
    data_path = current_path / 'data/characters.json'
    with open(data_path) as _file:
        characters = json.load(_file)
    return characters
