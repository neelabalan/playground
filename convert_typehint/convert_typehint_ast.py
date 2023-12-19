import ast

class TypingToBuiltinTransformer(ast.NodeTransformer):
    type_conversion_map = {
        'List': 'list',
        'Dict': 'dict',
        'Tuple': 'tuple',
        'Type': 'type'
    }
    def visit_ImportFrom(self, node):
        if node.module == 'typing':
            # Filter out specific imports from 'typing'
            node.names = [name for name in node.names if name.name not in ['List', 'Dict', 'Tuple']]
            if not node.names:
                # If no names are left, remove the import statement
                return None
        return node

    def visit_Subscript(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.Name):
            node.value.id = self.type_conversion_map.get(node.value.id, node.value.id)
        return node

def convert_typing_to_builtin(source_code):
    tree = ast.parse(source_code)
    transformer = TypingToBuiltinTransformer()
    new_tree = transformer.visit(tree)
    return ast.unparse(new_tree)
