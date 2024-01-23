import unittest

from field_search_json import get_json_field_map


class TestGetJsonFieldMap(unittest.TestCase):
    def setUp(self):
        self.json_obj = {
            'name': 'John',
            'age': 30,
            'city': 'New York',
            'details': {'hobby': 'reading', 'pet': {'name': 'Fluffy', 'type': 'cat'}},
            'newage': {'age': 33},
        }

    def test_get_json_field_map(self):
        self.assertEqual(get_json_field_map(self.json_obj, 'name'), ['name', 'details.pet.name'])
        self.assertEqual(get_json_field_map(self.json_obj, 'hobby'), ['details.hobby'])
        self.assertEqual(get_json_field_map(self.json_obj, 'city'), ['city'])
        self.assertEqual(get_json_field_map(self.json_obj, 'type'), ['details.pet.type'])
        self.assertEqual(get_json_field_map(self.json_obj, 'age'), ['age', 'newage.age'])
        self.assertEqual(get_json_field_map(self.json_obj, 'nonexistent'), [])


if __name__ == '__main__':
    unittest.main()
