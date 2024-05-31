import typing

import pydantic
import rdflib
from rdflib.namespace import OWL
from rdflib.namespace import RDF
from rdflib.namespace import RDFS


class OntologyTerm(pydantic.BaseModel):
    name: str
    namespace: typing.Any = pydantic.Field(default_factory=rdflib.Namespace)
    graph: typing.Any = pydantic.Field(default_factory=rdflib.Graph)
    # uri: typing.Optional[rdflib.URIRef] = None

    def add_to_graph(self, graph: rdflib.Graph) -> rdflib.Graph:
        # if self.uri is None:
        #     self.uri = self.construct_uri()
        self.graph.add_(self.construct_uri(), RDF.type, rdflib.URIRef(self.uri))
        return graph

    def construct_uri(self) -> rdflib.URIRef:
        return self.namespace[self.name]


class OwlClass(OntologyTerm):
    def add_to_graph(self) -> rdflib.Graph:
        uri_ref = self.construct_uri()
        self.graph.add((uri_ref, RDF.type, OWL.Class))
        self.graph.add((uri_ref, RDFS.label, rdflib.Literal(self.name)))
        return self.graph


class SubClass(OntologyTerm):
    parent_class: str

    def add_to_graph(self) -> rdflib.Graph:
        uri_ref = self.construct_uri()
        parent_uri = rdflib.URIRef(self.parent_class)
        self.graph.add((uri_ref, RDF.type, OWL.Class))
        self.graph.add((uri_ref, RDFS.label, rdflib.Literal(self.name)))
        self.graph.add((uri_ref, RDFS.subClassOf, parent_uri))
        return self.graph


class DataProperty(OntologyTerm):
    domain: str
    property_range: typing.Optional[typing.Any]

    def add_to_graph(self) -> rdflib.Graph:
        uri_ref = self.construct_uri()
        # assuming that namespace is going to be there
        domain_ref = self.namespace[self.domain]

        self.graph.add((uri_ref, RDF.type, OWL.DatatypeProperty))
        # self.graph.add((uri_ref, RDFS.label, rdflib.Literal(self.name)))
        self.graph.add((uri_ref, RDFS.domain, domain_ref))
        if self.property_range:
            range_ref = rdflib.URIRef(self.property_range)
            self.graph.add((uri_ref, RDFS.range, range_ref))
        return self.graph


class ObjectProperty(OntologyTerm):
    domain: str
    property_range: str

    def add_to_graph(self) -> rdflib.Graph:
        uri_ref = self.construct_uri()
        domain_ref = self.namespace[self.domain]
        range_ref = self.namespace[self.property_range]

        self.graph.add((uri_ref, RDF.type, OWL.ObjectProperty))
        self.graph.add((uri_ref, RDFS.label, rdflib.Literal(self.name)))
        self.graph.add((uri_ref, RDFS.domain, domain_ref))
        self.graph.add((uri_ref, RDFS.range, range_ref))
        return self.graph


class OntologyBuilder:
    TYPE_MAPPING = {
        str: None,  # default Literal
        int: rdflib.XSD.integer,
        float: rdflib.XSD.float,
        bool: rdflib.XSD.boolean,
    }

    def __init__(self, namespace: str, graph: rdflib.Graph):
        self.namespace = namespace
        if graph is None:
            self.graph = rdflib.Graph()
        else:
            self.graph = graph

    def define_classes(self, names: list[str]):
        for name in names:
            self.graph = OwlClass(name=name, namespace=self.namespace, graph=self.graph).add_to_graph()

    def define_subclasses(self, subclass_parent_class: list[tuple[str, str]]):
        for subclass, parent_class in subclass_parent_class:
            self.graph = SubClass(name=subclass, parent_class=parent_class, namespace=self.namespace, graph=self.graph).add_to_graph()

    def define_data_properties_from_model(self, model: typing.Type[pydantic.BaseModel], domain: str):
        for field_name, field_type in typing.get_type_hints(model).items():
            self.graph = DataProperty(name=field_name, namespace=self.namespace, graph=self.graph, domain=domain, property_range=self.TYPE_MAPPING.get(field_type)).add_to_graph()

    def define_object_property(self, name: str, domain: str, property_range: str):
        self.graph = ObjectProperty(name=name, namespace=self.namespace, graph=self.graph, domain=domain, property_range=property_range).add_to_graph()

    def build(): ...

    def serialize(self, path: str):
        self.graph.serialize(destination=path, format='turtle')
