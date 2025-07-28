"""
dependency : requests, colorama, beautifulsoup
run        : python stoicquote --color blue
"""

import argparse

import colorama
import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    colorama.init()
    bprint = lambda string: print('\033[94m' + string + '\033[0m')
    rprint = lambda string: print('\033[91m' + string + '\033[0m')
    yprint = lambda string: print('\033[93m' + string + '\033[0m')
    gprint = lambda string: print('\033[92m' + string + '\033[0m')

    r = requests.get('https://www.lettersfromastoic.net')
    soup = BeautifulSoup(r.content, 'html5lib')
    table = soup.find(id='w_quotescollection_2')
    quote = str(table.find('p'))
    quotefmt = quote[3 : quote.index('<a')] + '\n -- ' + quote[quote.index('>L') + 1 : quote.index('</')]

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--color', help='provide unique github user as arguement')
    colormap = {'blue': bprint, 'red': rprint, 'yellow': yprint, 'green': gprint}
    args = parser.parse_args()
    if args:
        colormap.get(args.color)(quotefmt)
