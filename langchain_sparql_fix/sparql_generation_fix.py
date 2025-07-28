import re
from typing import Any
from typing import Optional
from typing import Union

# https://python.langchain.com/docs/use_cases/graph/integrations/graph_sparql_qa
from langchain.chains import GraphSparqlQAChain
from langchain_core.callbacks import CallbackManagerForChainRun

CODE_BLOCK_PATTERN = r'```[ \t]*(\w+)?[ \t]*\r?\n(.*?)\r?\n[ \t]*```'
UNKNOWN = 'unknown'


def content_str(content: Union[str, list, None]) -> str:
    """Converts `content` into a string format.

    This function processes content that may be a string, a list of mixed text and image URLs, or None,
    and converts it into a string. Text is directly appended to the result string, while image URLs are
    represented by a placeholder image token. If the content is None, an empty string is returned.

    Args:
        - content (Union[str, List, None]): The content to be processed. Can be a string, a list of dictionaries
                                      representing text and image URLs, or None.

    Returns:
        str: A string representation of the input content. Image URLs are replaced with an image token.

    Note:
    - The function expects each dictionary in the list to have a "type" key that is either "text" or "image_url".
      For "text" type, the "text" key's value is appended to the result. For "image_url", an image token is appended.
    - This function is useful for handling content that may include both text and image references, especially
      in contexts where images need to be represented as placeholders.
    """
    if content is None:
        return ''
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        raise TypeError(f'content must be None, str, or list, but got {type(content)}')

    rst = ''
    for item in content:
        if not isinstance(item, dict):
            raise TypeError('Wrong content format: every element should be dict if the content is a list.')
        assert 'type' in item, "Wrong content format. Missing 'type' key in content's dict."
        if item['type'] == 'text':
            rst += item['text']
        elif item['type'] == 'image_url':
            rst += '<image>'
        else:
            raise ValueError(f"Wrong content format: unknown type {item['type']} within the content")
    return rst


# https://github.com/microsoft/autogen/blob/8f6590e2313cf937f8bf18ca02c767ca871729d3/autogen/code_utils.py#L99
def extract_code(
    text: Union[str, list], pattern: str = CODE_BLOCK_PATTERN, detect_single_line_code: bool = False
) -> list[tuple[str, str]]:
    """Extract code from a text.

    Args:
        text (str or List): The content to extract code from. The content can be
            a string or a list, as returned by standard GPT or multimodal GPT.
        pattern (str, optional): The regular expression pattern for finding the
            code block. Defaults to CODE_BLOCK_PATTERN.
        detect_single_line_code (bool, optional): Enable the new feature for
            extracting single line code. Defaults to False.

    Returns:
        list: A list of tuples, each containing the language and the code.
          If there is no code block in the input text, the language would be "unknown".
          If there is code block but the language is not specified, the language would be "".
    """
    text = content_str(text)
    if not detect_single_line_code:
        match = re.findall(pattern, text, flags=re.DOTALL)
        return match if match else [(UNKNOWN, text)]

    # Extract both multi-line and single-line code block, separated by the | operator
    # `([^`]+)`: Matches inline code.
    code_pattern = re.compile(CODE_BLOCK_PATTERN + r'|`([^`]+)`')
    code_blocks = code_pattern.findall(text)

    # Extract the individual code blocks and languages from the matched groups
    extracted = []
    for lang, group1, group2 in code_blocks:
        if group1:
            extracted.append((lang.strip(), group1.strip()))
        elif group2:
            extracted.append(('', group2.strip()))

    return extracted


class GraphSparqlChain(GraphSparqlQAChain):
    def _call(
        self,
        inputs: dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> dict[str, str]:
        """
        Generate SPARQL query, use it to retrieve a response from the gdb and answer
        the question.
        """
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()
        prompt = inputs[self.input_key]

        _intent = self.sparql_intent_chain.run({'prompt': prompt}, callbacks=callbacks)
        intent = _intent.strip()

        if 'SELECT' in intent and 'UPDATE' not in intent:
            sparql_generation_chain = self.sparql_generation_select_chain
            intent = 'SELECT'
        elif 'UPDATE' in intent and 'SELECT' not in intent:
            sparql_generation_chain = self.sparql_generation_update_chain
            intent = 'UPDATE'
        else:
            raise ValueError(
                'I am sorry, but this prompt seems to fit none of the currently '
                'supported SPARQL query types, i.e., SELECT and UPDATE.'
            )

        _run_manager.on_text('Identified intent:', end='\n', verbose=self.verbose)
        _run_manager.on_text(intent, color='green', end='\n', verbose=self.verbose)

        generated_sparql = sparql_generation_chain.run(
            {'prompt': prompt, 'schema': self.graph.get_schema}, callbacks=callbacks
        )
        # change here
        generated_sparql = extract_code(generated_sparql)[0][1]

        _run_manager.on_text('Generated SPARQL:', end='\n', verbose=self.verbose)
        _run_manager.on_text(generated_sparql, color='green', end='\n', verbose=self.verbose)

        if intent == 'SELECT':
            context = self.graph.query(generated_sparql)

            _run_manager.on_text('Full Context:', end='\n', verbose=self.verbose)
            _run_manager.on_text(str(context), color='green', end='\n', verbose=self.verbose)
            result = self.qa_chain(
                {'prompt': prompt, 'context': context},
                callbacks=callbacks,
            )
            res = result[self.qa_chain.output_key]
        elif intent == 'UPDATE':
            self.graph.update(generated_sparql)
            res = 'Successfully inserted triples into the graph.'
        else:
            raise ValueError('Unsupported SPARQL query type.')

        chain_result: dict[str, Any] = {self.output_key: res}
        if self.return_sparql_query:
            chain_result[self.sparql_query_key] = generated_sparql
        return chain_result
