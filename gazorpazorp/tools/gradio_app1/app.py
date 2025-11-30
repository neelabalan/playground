import gradio as gr
from common.load_data import load_characters

characters = load_characters()
# Load JSON data into a dictionary for easier access
character_dict = {character['name']: character for character in characters}


# Define a function to fetch character details
def get_character_details(character_name):
    character = character_dict.get(character_name, {})
    return character


# Create a dropdown menu of character names
dropdown = gr.Dropdown(choices=list(character_dict.keys()), label='Select a Character')

# Create Gradio interface
interface = gr.Interface(
    fn=get_character_details,
    inputs=dropdown,
    outputs='json',
    title='Rick and Morty Character Details',
    description='Select a character to see their details.',
)

# Run the app
if __name__ == '__main__':
    interface.launch(server_name='0.0.0.0', server_port=7860)
