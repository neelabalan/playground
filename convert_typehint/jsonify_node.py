# %%
import ast
import json
from typing import Any
from typing import Union


def ast_to_dict(node: Union[ast.AST, list[ast.AST], Any]) -> Union[dict[str, Any], list[Any], Any]:
    if isinstance(node, ast.AST):
        node_dict = {'_type': node.__class__.__name__}
        for field in node._fields:
            value = getattr(node, field, None)
            node_dict[field] = ast_to_dict(value)
        return node_dict
    elif isinstance(node, list):
        return [ast_to_dict(n) for n in node]
    else:
        return node


# %%
def run():
    with open('sample_code.py', 'r') as _file:
        ast_dict = ast_to_dict(ast.parse(_file.read()))
        with open('ast_sample_code.json', 'w') as _json_file:
            json.dump(ast_dict, _json_file, indent=4)


# %%
# run()
