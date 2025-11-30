import json

from rdflib import Graph
from textual import on
from textual.app import App
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button
from textual.widgets import Input
from textual.widgets import TextArea


def execute_query(ttl_file, sparql_query):
    """
    Executes a SPARQL query on a given TTL file and returns the results as a list of lists.
    Args:
        ttl_file: Path to the TTL file containing the RDF data.
        sparql_query: The SPARQL query string.
    Returns:
        A list of lists representing the tabular results.
    """
    graph = Graph()
    graph.parse(ttl_file, format='ttl')

    try:
        results = graph.query(sparql_query)
        results = json.loads(results.serialize(format='json').decode())
        bindings = results['results']['bindings']
    except Exception as e:
        print(f'Error executing query: {e}')
        return []
    return json.dumps(bindings, indent=4)


class SparqlQueryApp(App):
    BINDINGS = [
        ('q', 'quit', 'Quit'),
        ('s', 'submit', 'Submit SPARQL query'),
    ]

    def __init__(self, ttl_file_path):
        super().__init__()
        self.ttl_file_path = ttl_file_path
        self.graph = Graph().parse(self.ttl_file_path, format='turtle')
        self.query_input = TextArea(name='query')
        self.result_area = TextArea(read_only=True)
        self.submit_button = Button('Submit')

    def compose(self) -> ComposeResult:
        with Container():
            yield self.query_input
            yield self.result_area
            yield self.submit_button

    @on(Button.Pressed)
    def on_button_pressed(self, event):
        if event.button == self.submit_button:
            query = self.query_input.text
            results = execute_query(self.ttl_file_path, query)
            self.result_area.text = results


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print('Usage: python sparql_app.py <path_to_ttl_file>')
        sys.exit(1)
    app = SparqlQueryApp(sys.argv[1])
    app.run()
