import ast

class TypingToBuiltinTransformer(ast.NodeTransformer):
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
            if node.value.id == 'List':
                node.value.id = 'list'
            elif node.value.id == 'Dict':
                node.value.id = 'dict'
            elif node.value.id == 'Tuple':
                node.value.id = 'tuple'
        return node

def convert_typing_to_builtin(source_code):
    tree = ast.parse(source_code)
    transformer = TypingToBuiltinTransformer()
    new_tree = transformer.visit(tree)
    return ast.unparse(new_tree)
