import ast
import typing


class FunctionExtractor(ast.NodeVisitor):
    def __init__(self, keywords):
        self.keywords = keywords
        self.functions = []

    def visit_FunctionDef(self, node):
        if all(keyword.lower() in ast.unparse(node).lower() for keyword in self.keywords):
            self.functions.append(ast.unparse(node))
        self.generic_visit(node)


def extract_functions(source_code: str, keywords: typing.List[str]):
    tree = ast.parse(source_code)
    extractor = FunctionExtractor(keywords)
    extractor.visit(tree)
    return extractor.functions


if __name__ == '__main__':
    with open('test.py', 'r') as _file:
        source_code = _file.read()
    print(extract_functions(source_code, ['funny', 'joke']))
    print(extract_functions(source_code, ['test']))
