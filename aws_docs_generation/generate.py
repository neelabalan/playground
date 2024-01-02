import inspect
import json
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import boto3
import boto3.session
from botocore.model import Shape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def remove_p_tags(value: str) -> str:
    return value.replace('<p>', '').replace('</p>', '')


class AwsServiceDocumenter:
    def __init__(self, client):
        self._client = client

    def traverse_and_document(self, shape: Shape, history: List[str] = None) -> Dict[str, Any] | str:
        if history is None:
            history = []

        result = {}

        if shape.name in history:
            return '{...recursive...}'
        else:
            history.append(shape.name)

            for key, _value in shape.members.items():
                if _value.type_name == 'map' and hasattr(_value.value, 'members'):
                    result[key] = self.traverse_and_document(_value.value, history=history.copy())
                elif _value.type_name == 'structure' and hasattr(_value, 'members'):
                    result[key] = self.traverse_and_document(_value, history=history.copy())
                elif _value.type_name == 'list' and hasattr(_value, 'member') and _value.member.type_name != 'string':
                    result[key] = [self.traverse_and_document(_value.member, history=history.copy())]
                else:
                    result[key] = {
                        'description': remove_p_tags(_value.documentation) if hasattr(_value, 'documentation') else None,
                        'type': _value.type_name,
                    }
                    if hasattr(_value, 'enum') and _value.enum:
                        result[key].update({'enum': _value.enum})

            history.pop()

        return result

    def process_method(self, method_name: str) -> Optional[Dict[str, str]]:
        service_model = self._client.meta.service_model
        if method_name not in self._client.meta.method_to_api_mapping:
            return
        operation_name = self._client.meta.method_to_api_mapping[method_name]
        operation_model = service_model.operation_model(operation_name)
        method_map: Dict[str, str] = {
            'method_name': method_name,
            'method_documentation': remove_p_tags(operation_model.documentation),
        }
        try:
            if hasattr(operation_model.input_shape, 'members'):
                method_map.update({'method_request_schema': self.traverse_and_document(operation_model.input_shape)})
            if hasattr(operation_model.output_shape, 'members'):
                method_map.update(
                    {
                        'method_response_schema': self.traverse_and_document(operation_model.output_shape),
                    }
                )

        except Exception as ex:
            logger.info(f'Error encountered while processing for {method_name} - {ex}')
            return
        return method_map

    def get_instance_public_methods(self, instance):
        instance_members = inspect.getmembers(instance)
        instance_methods = {}
        for name, member in instance_members:
            if not name.startswith('_'):
                if inspect.ismethod(member):
                    instance_methods[name] = member
        return instance_methods

    def document(self, service: str) -> Dict[str, List[Dict]]:
        docs_map = {
            service: {
                'class_name': self._client.__class__.__name__,
                'documentation': remove_p_tags(self._client.meta.service_model.documentation),
                'methods': [],
            }
        }
        available_methods_map = self.get_instance_public_methods(self._client)

        for method_name, method in available_methods_map.items():
            logger.info(f'{method_name=}')
            method_doc = self.process_method(method_name)
            if method_doc:
                docs_map[service]['methods'].append(method_doc)
        return docs_map


def run():
    region_name = 'us-east-1'
    session = boto3.session.Session(region_name=region_name)
    services = session.get_available_services()
    for service in services[1:10]:
        # client = session.create_client(
        #     service,
        #     region_name=region_name,
        #     aws_access_key_id="foo",
        #     aws_secret_access_key="bar",
        # )
        client = session.client(service)
        service_documenter = AwsServiceDocumenter(client)
        service_docs = service_documenter.document(service)
        with open(f'docs/{service}.json', 'w') as file:
            json.dump(service_docs, file)


if __name__ == '__main__':
    run()
