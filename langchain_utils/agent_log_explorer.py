import json
import pathlib
import string
from typing import Any
from typing import Dict
from typing import NoReturn
from typing import Tuple

import gradio as gr

steps_template = string.Template(
    """
# Step $step_number\n\n
## Log\n ```\n$log\n```\n
## Tool\n ```\n$tool\n```\n
## Tool Input\n ```\n$tool_input\n```\n
## Output\n ```\n$output\n```\n
"""
)


def remove_backticks_from_string(text: str) -> str | Any:
    if isinstance(text, str):
        return text.replace('`', '')
    else:
        return text


def load_json(directory_path: str | pathlib.Path) -> str | NoReturn:
    file_path = pathlib.Path(directory_path)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return json.dumps(data, indent=4)
    except Exception as e:
        return f'Error loading JSON: {e}'


def update_dropdown(directory_path: str) -> gr.Dropdown:
    path = pathlib.Path(directory_path)
    if not path.exists() or not path.is_dir():
        raise Exception('Directory does not exist.')
    if not directory_path:
        return 'Please select a directory.'
    return gr.Dropdown.update(choices=list(path.glob('*.json')))


def explore_json(input_json: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str], str]:
    input_query = input_json['input']
    final_output = input_json['output']
    steps = input_json['intermediate_steps']

    # Generate UI components for each step
    steps_ui = []
    for i, step in enumerate(steps, start=1):
        step['log'] = remove_backticks_from_string(step['log'])
        step['tool'] = remove_backticks_from_string(step['tool'])
        step['tool_input'] = remove_backticks_from_string(step['tool_input'])
        step['output'] = remove_backticks_from_string(step['output'])
        step_ui = steps_template.substitute(
            step_number=i,
            log=step['log'],
            tool=step['tool'],
            tool_input=step['tool_input'],
            output=step['output'],
        )
        steps_ui.append(step_ui)

    return input_query, final_output, '\n\n'.join(steps_ui)


if __name__ == '__main__':
    with gr.Blocks() as demo:
        gr.Markdown('LangChain Agent log explorer')
        with gr.Row():
            dir_path = gr.Textbox(label='Directory path')
            read_dir = gr.Button(label='Submit')

        # directory_input = gr.FileExplorer(label="Select Directory", file_count='directory')
        file_dropdown = gr.Dropdown(label='Select JSON File', choices=[], value=None)
        read_dir.click(update_dropdown, inputs=dir_path, outputs=file_dropdown)
        submit_button = gr.Button('Explore JSON')

        with gr.Accordion('Agent Raw Response'):
            json_input = gr.JSON(label='JSON', lines=20, readonly=True)
        input_query = gr.Textbox(label='Input Query', readonly=True)
        final_output = gr.Textbox(label='Final Output', readonly=True)

        file_dropdown.change(load_json, inputs=file_dropdown, outputs=json_input)

        with gr.Accordion('Intermediate Steps'):
            steps_output = gr.Markdown()

        # Function call on button click
        submit_button.click(
            explore_json,
            inputs=[json_input],
            outputs=[input_query, final_output, steps_output],
        )

    demo.launch(show_error=True, debug=True)
