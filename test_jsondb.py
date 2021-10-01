import pytest
import os
import json
from jsondb import jsondb
# utils
def dummy_func():
	pass

def test_iscallable():
	assert jsondb.is_callable(dummy_func)
	assert not jsondb.is_callable(int)
	assert not jsondb.is_callable('hello')


# jsondb
@pytest.fixture
def db():
	return jsondb.load('db')

def test_load():
	# this works
	db = jsondb.load('db')

	# this should not
	with pytest.raises(Exception) as e:
		db = jsondb.load('/doesnotexist')

def test_get(db):
	assert db.get('products')

def test_new_and_drop(db):
	test = db.new('test')
	assert test.path	
	db.drop(test)
	assert not os.path.exists(test.path)

def test_insert_and_dumps(db):
	doc = [{'key': 'value'}]
	test = db.new('test')
	#insert
	test.insert(doc)
	assert test.find(lambda x: x['key']=='value') == doc
	# dump
	test.dump()
	# load and check
	with open(test.path, 'r') as file:
		json.load(file) == doc

# collection
def test_find(db):
	restaurant = db.get('restaurant')
	assert restaurant.find(lambda x: x.get("address")== "228 City Road") == \
	[{
		"URL": "http://www.just-eat.co.uk/restaurants-cn-chinese-cardiff/menu",
		"_id": {
			"$oid": "55f14312c7447c3da7051b26"
		},
		"address": "228 City Road",
		"address line 2": "Cardiff",
		"name": ".CN Chinese",
		"outcode": "CF24",
		"postcode": "3JH",
		"rating": 5,
		"type_of_food": "Chinese"
	}]

def test_delete(db):
	restaurant = db.get('restaurant')
	doc = [{
		"URL": "http://www.just-eat.co.uk/restaurants-cn-chinese-cardiff/menu",
		"_id": {
			"$oid": "55f14312c7447c3da7051b26"
		},
		"address": "228 City Road",
		"address line 2": "Cardiff",
		"name": ".CN Chinese",
		"outcode": "CF24",
		"postcode": "3JH",
		"rating": 5,
		"type_of_food": "Chinese"
	}]
	# document present
	assert restaurant.find(lambda x: x.get("address")== "228 City Road") == doc 

	# delete the document
	restaurant.delete(lambda x: x.get("address")== "228 City Road") 

	# check if it is not there
	assert not restaurant.find(lambda x: x.get("address")== "228 City Road") == doc 
	# since no dump is called changes not written to file


def test_update(db):
	doc = [
		{'key': 'value1'}, 
		{'key': 'value2'}
	]
	test = db.new('test')
	test.insert(doc)
	def func(document):
		document.update({'key': 'newvalueadded'})
		return document

	test.update(func, lambda x: x['key'] == 'value2')
	assert test.collection ==  [
		{'key': 'value1'}, 
		{'key': 'newvalueadded'}
	]