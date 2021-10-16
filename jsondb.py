import json
import os
from json import JSONDecodeError
from typing import List, Dict, Callable
from pathlib import Path


class PathNotFoundError(Exception):
    pass


class DuplicateEntryError(Exception):
    pass


def is_callable(obj):
    return "__call__" in dir(obj)


def load(dbpath):
    path = Path(dbpath)
    collections = dict()
    collections["root"] = path

    if not path.exists():
        raise PathNotFoundError("The provided path does not exists")
    if not path.is_dir():
        raise Exception("Path to *directory* is not provided")

    for path in path.iterdir():
        collections[path.stem] = path.resolve()
    return jsondb(collections)


class jsondb:
    def __init__(self, collections: Dict):
        self.collections = collections
        self.dbpath = collections.get("root")

    def get(self, name: str, index=[]):
        if self.collections:
            return collection(self.collections.get(name), index)
        else:
            raise Exception("collections not loaded")

    def new(self, name, indices=[]):
        if not type(name) == str:
            raise TypeError('collection name must be of type "str"')
        collection_path = self.dbpath / "{}.json".format(name)
        with open(collection_path, "w") as jsonfile:
            json.dump([], jsonfile)
        # update collections
        self.collections[name] = collection_path
        return collection(collection_path, indices=indices)

    def drop(self, collection):
        # delete collection
        collection.drop()
        return self.collections.pop(str(collection))


class collection:
    def __init__(self, path, indices=[]):
        self.path = path
        self.indices = indices
        try:
            with open(self.path, "r") as jsonfile:
                self.collection = json.load(jsonfile)
        except JSONDecodeError as decode_error:
            print("Error loading JSON document: {}".format(decode_error))

    def __str__(self):
        return self.path.stem

    def drop(self):
        self.path.unlink()
        del self

    def find(self, predicate: Callable, return_index=False) -> List[Dict]:
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
            raise TypeError("arument provided is not callable")

    def duplicate_entry_exists(self, document):
        if not self.indices:
            return False

        flag = False
        for index in self.indices:
            doc = self.find(lambda x: x.get(index) == document[0].get(index))
            if doc:
                flag = True
        return flag

    def insert(self, document: List) -> List[Dict]:
        if not self.duplicate_entry_exists(document):
            self.collection.extend(document)
            self.dump()
            return document
        else:
            raise DuplicateEntryError("something")

    def delete(self, predicate: Callable) -> List[Dict]:
        # use index to remove with pop in list
        documents = self.find(predicate, return_index=True)
        popped_docs = list()
        for index, document in documents:
            popped_docs.append(self.collection.pop(index))
        self.dump()
        return popped_docs

    def update(self, func, predicate) -> List[Dict]:
        documents = self.find(predicate, return_index=True)
        for index, document in documents:
            # func should return a dict
            self.collection[index] = func(document)
        self.dump()

    def dump(self, indent=False):
        with open(self.path, "w") as jsonfile:
            if indent:
                json.dump(self.collection, jsonfile, indent=4)
            else:
                json.dump(self.collection, jsonfile)

    def dumps(self, indent=False):
        if indent:
            return json.dumps(self.collection)
        else:
            return json.dumps(self.collection, indent=4)
