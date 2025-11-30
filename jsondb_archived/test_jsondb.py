import json
import os

import pytest
from jsondb import DuplicateEntryError
from jsondb import is_callable
from jsondb import jsondb

products = [
    {
        '_id': 'ac3',
        'name': 'AC3 Phone',
        'brand': 'ACME',
        'type': 'phone',
        'price': 200,
        'rating': 3.8,
        'warranty_years': 1,
        'available': True,
    },
    {
        '_id': 'ac7',
        'name': 'AC7 Phone',
        'brand': 'ACME',
        'type': 'phone',
        'price': 320,
        'rating': 4,
        'warranty_years': 1,
        'available': False,
    },
    {
        '_id': {'$oid': '507d95d5719dbef170f15bf9'},
        'name': 'AC3 Series Charger',
        'type': ['accessory', 'charger'],
        'price': 19,
        'rating': 2.8,
        'warranty_years': 0.25,
        'for': ['ac3', 'ac7', 'ac9'],
    },
    {
        '_id': {'$oid': '507d95d5719dbef170f15bfa'},
        'name': 'AC3 Case Green',
        'type': ['accessory', 'case'],
        'color': 'green',
        'price': 12,
        'rating': 1,
        'warranty_years': 0,
    },
]


# utils
def dummy_func():
    pass


def test_iscallable():
    assert is_callable(dummy_func)
    assert not is_callable(int)
    assert not is_callable('hello')


# jsondb
@pytest.fixture
def db():
    db = jsondb('db/test.json')
    yield db
    if os.path.exists(db.path):
        db.drop()


def test_load():
    # this works
    db = jsondb('db/products.json')

    # this should not
    with pytest.raises(Exception) as e:
        db = jsondb('/doesnotexist')


def test_new_and_drop(db):
    assert db.path
    db.drop()
    assert not os.path.exists(db.path)


def test_insert_and_commit(db):
    doc = [{'key': 'value'}]
    # insert
    db.insert(doc)
    assert db.find(lambda x: x['key'] == 'value') == doc
    # dump
    db.commit()
    # load and check
    with open(db.path, 'r') as file:
        json.load(file) == doc


def test_find(db):
    db.insert(products)
    assert db.find(lambda x: x.get('price') == 200) == [
        {
            '_id': 'ac3',
            'name': 'AC3 Phone',
            'brand': 'ACME',
            'type': 'phone',
            'price': 200,
            'rating': 3.8,
            'warranty_years': 1,
            'available': True,
        }
    ]


def test_delete(db):
    doc = [
        {
            'URL': 'http://www.just-eat.co.uk/restaurants-cn-chinese-cardiff/menu',
            '_id': {'$oid': '55f14312c7447c3da7051b26'},
            'address': '228 City Road',
            'address line 2': 'Cardiff',
            'name': '.CN Chinese',
            'outcode': 'CF24',
            'postcode': '3JH',
            'rating': 5,
            'type_of_food': 'Chinese',
        }
    ]
    # document present
    db.insert(doc)
    assert db.find(lambda x: x.get('address') == '228 City Road') == doc

    # delete the document
    db.delete(lambda x: x.get('address') == '228 City Road')

    # check if it is not there
    assert not db.find(lambda x: x.get('address') == '228 City Road') == doc
    # since no dump is called changes not written to file
    db.drop()


def test_update(db):
    doc = [{'key': 'value1'}, {'key': 'value2'}]
    db.insert(doc)

    def func(document):
        document.update({'key': 'newvalueadded'})
        return document

    db.update(func, lambda x: x['key'] == 'value2')
    assert db.collection == [{'key': 'value1'}, {'key': 'newvalueadded'}]
    db.drop()


def test_duplicate_entry(db):
    db.insert([{'key': 'value'}])
    db.set_index('key')
    with pytest.raises(DuplicateEntryError) as e:
        db.insert([{'key': 'value'}])

    db.insert([{'key': 'someothervalue'}])
