import random
import sys
import pkg_resources

from rich.console import Console
from rich.panel import Panel

console = Console()

def get_random_quote():
    ''' returns a random quote in list format'''
    content = pkg_resources.resource_string(__name__, 'data/quotes').decode()
    # with open('data/quotes', 'r') as file:
    # content = file.read()
    quotelist = content.split('\n')
    random_number = random.randrange(0, 400, 4)
    return quotelist[random_number : random_number+3]

def display_quote(quote, author, source, color):
    console.print(
        Panel(
            '''[{color}]{}[/{color}]\n\n[italic {color}]{}\n{}[/italic {color}]'''.format(
                quote, 
                author, 
                source, 
                color=color
            ), 
            title='Stoic quote'
        ), 
        style=color
    )

def main():
    quote, author, source = get_random_quote()
    color = sys.argv[1] if len(sys.argv)>1 else 'white'
    display_quote(quote, author, source, color)

if __name__ == '__main__':
    main()
