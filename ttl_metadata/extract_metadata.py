import argparse
import json
from typing import Dict
from typing import List

from pydantic import BaseModel
from rdflib import OWL
from rdflib import RDF
from rdflib import RDFS
from rdflib import Graph
from rdflib import URIRef


class Property(BaseModel):
    name: str
    values: List[str]


class ClassMetadata(BaseModel):
    uri: str
    subclasses: List[str]
    object_properties: Dict[str, Property]
    datatype_properties: Dict[str, Property]


class MetadataExtractor:
    def __init__(self, file):
        self.g = Graph()
        self.g.parse(file, format='ttl')

    def add_properties(self, subject, prop_type, metadata_dict):
        for prop in self.g.subjects(RDF.type, prop_type):
            prop_name = str(prop).split('/')[-1]
            for domain in self.g.objects(prop, RDFS.domain):
                domain_name = str(domain).split('/')[-1]
                if domain_name in metadata_dict:
                    if prop_name not in metadata_dict[domain_name].object_properties:
                        metadata_dict[domain_name].object_properties[prop_name] = Property(name=prop_name, values=[])
                    for range_class in self.g.objects(prop, RDFS.range):
                        metadata_dict[domain_name].object_properties[prop_name].values.append(str(range_class))

    def collect_classes_and_properties(self):
        ontology_metadata = {}
        for subject in self.g.subjects(RDF.type, OWL.Class):
            class_uri = str(subject)
            class_name = class_uri.split('/')[-1]
            ontology_metadata[class_name] = ClassMetadata(
                uri=class_uri,
                subclasses=[str(o).split('/')[-1] for o in self.g.subjects(RDFS.subClassOf, subject)],
                object_properties={},
                datatype_properties={},
            )
        self.add_properties(subject, OWL.ObjectProperty, ontology_metadata)
        self.add_properties(subject, OWL.DatatypeProperty, ontology_metadata)
        return ontology_metadata

    def extract(self):
        return self.collect_classes_and_properties()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some files.')
    parser.add_argument('--file', type=str, help='The input file to process')
    parser.add_argument('--out', type=str, help='The output file to write to')

    args = parser.parse_args()

    extractor = MetadataExtractor(args.file)
    ontology_metadata = extractor.extract()

    with open(args.out, 'w') as f:
        json.dump([class_metadata.model_dump() for class_metadata in ontology_metadata.values()], f, indent=4)
