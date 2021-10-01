import json
import os
from typing import List, Dict, Callable
from pathlib import Path


class PathDoesNotExist(Exception):
    pass


def is_callable(obj):
    return "__call__" in dir(obj)


def load(dbpath):
    path = Path(dbpath)
    collections = dict()
    collections["root"] = path

    if not path.exists():
        raise PathDoesNotExist("The provided path does not exists")
    if not path.is_dir():
        raise Exception("Path to directory is not provided")

    for path in path.iterdir():
        collections[path.stem] = path.resolve()
    return jsondb(collections)


class jsondb:
    def __init__(self, collections: Dict):
        self.collections = collections
        self.dbpath = collections.get("root")

    def get(self, name: str):  
        if self.collections:
            return collection(self.collections.get(name))
        else:
            raise Exception("collections not loaded")

    def new(self, name):
        if not type(name) == str:
            raise TypeError('collection name must be of type "str"')
        collection_path = self.dbpath / "{}.json".format(name)
        with open(collection_path, "w") as jsonfile:
            json.dump([], jsonfile)
        # update collections
        self.collections[name] = collection_path
        return collection(collection_path)

    def drop(self, collection):  
        # delete collection
        collection.drop()
        return self.collections.pop(str(collection))


class collection:
    def __init__(self, path):
        self.path = path
        try:
            with open(self.path, "r") as jsonfile:
                self.collection = json.load(jsonfile)
        except Exception as e:
            print("Error loading JSON document: {}".format(e))

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
            raise Exception("arument provided is not callable")

    def insert(self, document: List) -> List[Dict]:
        self.collection.extend(document)
        return document

    def delete(self, predicate: Callable) -> List[Dict]:
        # use index to remove with pop in list
        documents = self.find(predicate, return_index=True)
        popped_docs = list()
        for index, document in documents:
            popped_docs.append(self.collection.pop(index))
        return popped_docs

    def update(self, func, predicate) -> List[Dict]:
        documents = self.find(predicate, return_index=True)
        for index, document in documents:
            # func should return a dict
            self.collection[index] = func(document)  

    def dump(self):
        with open(self.path, "w") as jsonfile:
            json.dump(self.collection, jsonfile)

    def dumps(self):
        return json.dumps(self.collection)
