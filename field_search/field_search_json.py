import json


def get_json_field_map(json_obj, field_name, parent_key='', sep='.'):
    """
    Returns a list of strings of JSON field map for the given input.
    """
    field_map = []
    for k, v in json_obj.items():
        key = f'{parent_key}{k}{sep}'
        if isinstance(v, dict):
            field_map.extend(get_json_field_map(v, field_name, key))
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    field_map.extend(get_json_field_map(i, field_name, key))
        if k == field_name:
            field_map.append(key[:-1])
    return field_map
