import sys 
from datetime import datetime
try:
    from bs4 import BeautifulSoup
    from pytablewriter import MarkdownTableWriter
except ImportError as error:
    print('modules not found {}'.format(error))

line = []
md = []
writer = MarkdownTableWriter()
writer.headers = ["bookmarks", "date"]

inputfile = sys.argv[1]
outputfile = sys.argv[2]

with open(inputfile) as html:
    soup = BeautifulSoup(html.read())
    for dt in soup.find_all('a'):
        time = datetime.fromtimestamp(int(dt.get('add_date'))).strftime("%c")
        line.append("{}".format(time))
        line.append("[{0}]({1})".format(dt.text, dt.get('href')))
        md.append(line)
        line=[]

writer.value_matrix = md
with open(outputfile, 'w+') as of:
    of.write(writer.dumps())