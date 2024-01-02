import sys
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    from pytablewriter import MarkdownTableWriter
except ImportError as error:
    print(f'modules not found {error}')

line = []
md = []
writer = MarkdownTableWriter()
writer.headers = ['bookmarks', 'date']

inputfile = sys.argv[1]
outputfile = sys.argv[2]

with open(inputfile) as html:
    soup = BeautifulSoup(html.read())
    for dt in soup.find_all('a'):
        time = datetime.fromtimestamp(int(dt.get('add_date'))).strftime('%c')
        line.append(f'{time}')
        line.append(f"[{dt.text}]({dt.get('href')})")
        md.append(line)
        line = []

writer.value_matrix = md
with open(outputfile, 'w+') as of:
    of.write(writer.dumps())
