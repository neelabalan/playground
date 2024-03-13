from langchain.chains import GraphSparqlQAChain
from langchain_community.graphs import RdfGraph
from langchain_openai import ChatOpenAI
from sparql_generation_fix import GraphSparqlChain


def works():
    graph = RdfGraph(
        source_file="http://www.w3.org/People/Berners-Lee/card",
        standard="rdf",
        local_copy="test.ttl",
    )
    chain = GraphSparqlChain.from_llm(
        ChatOpenAI(temperature=0), graph=graph, verbose=True
    )
    chain.run("What is Tim Berners-Lee's work homepage?")
    chain.run(
        "Save that the person with the name 'Timothy Berners-Lee' has a work homepage at 'http://www.w3.org/foo/bar/'"
    )

def doesnt_work():
    # results in 
    # pyparsing.exceptions.ParseException: Expected {SelectQuery | ConstructQuery | DescribeQuery | AskQuery}, found '`'  (at char 0), (line:1, col:1)
    graph = RdfGraph(
        source_file="http://www.w3.org/People/Berners-Lee/card",
        standard="rdf",
        local_copy="test.ttl",
    )
    chain = GraphSparqlQAChain.from_llm(
        ChatOpenAI(temperature=0), graph=graph, verbose=True
    )
    chain.run("What is Tim Berners-Lee's work homepage?")
    chain.run(
        "Save that the person with the name 'Timothy Berners-Lee' has a work homepage at 'http://www.w3.org/foo/bar/'"
    )




if __name__ == "__main__":
    works()
    doesnt_work()
