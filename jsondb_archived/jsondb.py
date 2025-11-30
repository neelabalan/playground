import json
import os
import shelve
from json import JSONDecodeError
from pathlib import Path


def is_callable(obj):
    return '__call__' in dir(obj)


def load_index(path):
    name = path.stem
    if not path.exists():
        with shelve.open(str(path), 'c') as index:
            index[name] = set()
    with shelve.open(str(path), 'c') as index:
        return index.get(name), index.get('_id')


def load_collection(path):
    collection = list()
    if path.is_dir():
        raise DirPathProvidedError('File path not provided')
    if not path.exists():
        with open(path, 'w') as file:
            json.dump([], file)
            collection = []
    else:
        try:
            with open(path, 'r') as file:
                collection = json.load(file)
                if type(collection) != list:
                    raise TypeError('document not in List format')
        except JSONDecodeError as error:
            print('unable to decode JSON document')
    return collection


class PathNotFoundError(Exception):
    pass


class DuplicateEntryError(Exception):
    pass


class IndexValidationError(Exception):
    pass


class jsondb:
    def __init__(self, path: str):
        self.path = Path(path)
        self.collection = load_collection(self.path)
        self.index = index(self)

    def __str__(self):
        return self.path.stem

    def __len__(self):
        return len(self.collection)

    def set_index(self, field: str):
        self.index.create_index(field)

    def find(self, predicate, return_index=False):
        if is_callable(predicate):
            if return_index:
                filtered = list()
                for index, document in enumerate(self.collection):
                    doc = document if predicate(document) else None
                    if doc:
                        filtered.append((index, doc))
                return filtered
            else:
                return list(filter(predicate, self.collection))
        else:
            raise TypeError('argument provided is not callable')

    def insert(self, document):
        result, field = self.index._check_for_duplicate_entry(document)
        if not field:
            if '_id' in self.index.fields:
                for doc in document:
                    self.index.increment()
                    doc.update({'_id': self.index._id})
            self.collection.extend(document)
            self.commit()
            return document
        else:
            raise DuplicateEntryError('Duplicate entry of document found {} {}'.format(document, field))

    def delete(self, predicate):
        # use index to remove with pop in list
        documents = self.find(predicate, return_index=True)
        popped_docs = list()
        for index, document in documents:
            popped_docs.append(self.collection.pop(index))
        self.commit()
        return popped_docs

    def update(self, func, predicate):
        documents = self.find(predicate, return_index=True)
        for index, document in documents:
            # func should return a dict
            self.collection[index] = func(document)
        self.commit()

    def drop(self):
        Path(self.path).unlink()
        Path(self.index.index_path).unlink()

    def commit(self):
        with open(self.path, 'w') as jsonfile:
            json.dump(self.collection, jsonfile)


class index:
    def __init__(self, collection):
        self.collection = collection
        self.index_path = str(collection.path.parent / Path(str(collection) + '.index'))
        self.index_name = Path(self.index_path).stem
        self.fields, self._id = load_index(Path(self.index_path))

    def validate(self):
        for field in self.fields:
            distinct_fields = set()
            # iter
            for document in self.collection.collection:
                distinct_fields.add(document.get(field))
                # len
            if len(distinct_fields) != len(self.collection):
                raise IndexValidationError('Index fields {} not maintained in db'.format(self.fields))

    def create_index(self, field):
        with shelve.open(self.index_path, 'w') as index:
            if field == '_id' and not index.get('_id'):
                self.fields.add(field)
                index[self.index_name] = self.fields
                self._id = 0
                index['_id'] = self._id
            else:
                self.fields.add(field)
                index[self.index_name] = self.fields

    def increment(self, step=1):
        with shelve.open(self.index_path, 'w') as index:
            self._id += step
            index['_id'] = self._id

    def decrement(self, step=1):
        with shelve.open(self.index_path, 'w') as index:
            self._id -= step
            index['_id'] = self._id

    def _check_for_duplicate_entry(self, document):
        if not self.fields:
            return ([], '')

        for field in self.fields:
            doc = self.collection.find(lambda x: x.get(field) == document[0].get(field))
            if doc:
                return doc, field
        return [], ''

    def duplicate_entry_exists(self, document):
        document, field = self._check_for_duplicate_entry(document)
        return bool(field)
