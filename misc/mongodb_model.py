import typing

import bson
import pymongo
import pymongo.collection


class Model(dict):
    collection: typing.ClassVar[pymongo.collection.Collection]

    __getattr__ = dict.get
    __delattr__ = dict.__delitem__
    __setattr__ = dict.__setitem__

    def save(self) -> None:
        if not self._id:
            result = self.collection.insert_one(self)
            self['_id'] = result.inserted_id
        else:
            self.collection.replace_one({'_id': bson.ObjectId(self._id)}, self)

    def reload(self) -> None:
        if self._id:
            doc = self.collection.find_one({'_id': bson.ObjectId(self._id)})
            if doc:
                self.update(doc)

    def remove(self) -> None:
        if self._id:
            self.collection.delete_one({'_id': bson.ObjectId(self._id)})
            self.clear()

    @classmethod
    def find_all(cls) -> list[typing.Self]:
        return [cls(doc) for doc in cls.collection.find()]

    @classmethod
    def find_by_id(cls, id: str) -> typing.Self | None:
        doc = cls.collection.find_one({'_id': bson.ObjectId(id)})
        return cls(doc) if doc else None


class Document(Model):
    collection: typing.ClassVar[pymongo.collection.Collection] = pymongo.MongoClient()['test_database'][
        'test_collections'
    ]

    @property
    def keywords(self) -> list[str]:
        return self.title.split() if self.title else []


if __name__ == '__main__':
    documents = Document.find_all()
    for document in documents:
        print(document.title, document.keywords)

    document = Document({'title': 'test document', 'slug': 'test-document'})
    print(document._id)
    document.save()
    print(document._id)

    document = Document.find_by_id('50d3cb0068c0064a21e76be4')
    if document:
        print(document.title)

        document.title = 'test document 2'
        document.save()
        print(document.title)

        document.remove()
        print(document)
