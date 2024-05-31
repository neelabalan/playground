import pydantic
import rdflib
from main import OntologyBuilder


class PersonModel(pydantic.BaseModel):
    name: str
    age: int


class AuthorOntologyBuilder(OntologyBuilder):
    def __init__(self, namespace, graph):
        super().__init__(namespace, graph)

    def build(self):
        self.define_classes(['Person', 'Book'])
        self.define_data_properties_from_model(PersonModel, 'Person')
        self.define_object_property('authorOf', domain='Person', property_range='Book')


if __name__ == '__main__':
    NS = rdflib.Namespace('http://example.org#')
    builder = AuthorOntologyBuilder(NS, None)
    builder.build()
    builder.serialize('test.ttl')
