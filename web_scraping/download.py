import requests
import re
from bs4 import BeautifulSoup
from urllib import request
import colorama 
import os


# lambdas
colorama.init()
bprint = lambda string: print('\033[94m' + string + '\033[0m')
rprint = lambda string: print('\033[91m' + string + '\033[0m')
yprint = lambda string: print('\033[93m' + string + '\033[0m')
gprint = lambda string: print('\033[92m' + string + '\033[0m')

def get_paths(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    audiopaths = list()
    for a in soup.find_all('a', href=re.compile('http.*\.mp3')):
        audiopaths.append(a['href'])
    for a in soup.find_all('a', href=re.compile('http.*\.WAV')):
        audiopaths.append(a['href'])
    return audiopaths 

def get_size(content):
    mb  = 1048576
    try:
        return str(content.length/mb)
    except:
        rprint('unable to get the size of the file')

def filter_paths(audiopaths):
    filepaths = list()
    for path in audiopaths:
        filepaths.append(path.split('.com')[-1])
    return filepaths

def start_download(s3url, urls):

    filepaths = filter_paths(urls)
    current_path = os.getcwd()

    # creating directories
    for path in filepaths:
        abspath = current_path + path
        filename = os.path.basename(path)
        dir = os.path.dirname(abspath)

        if not os.path.exists(dir):
            os.makedirs(dir)
            bprint("--- created {0}".format(dir))

        try:
            lecture_url = s3url + path
            content = request.urlopen(str(lecture_url))
            bprint('downloading -- {0}'.format(filename))
            yprint('size - {0} MB'.format(get_size(content)))
            request.urlretrieve(lecture_url, abspath)
            gprint('downloaded and saved {0} at {1}'.format(filename, dir))
            print('\n\n')

        except:
            rprint('error while trying to download the file')
    
if __name__ == "__main__":
    rooturl = 'http://godasastry.in/discources'
    s3url = 'https://godasastry-2018.s3.ap-south-1.amazonaws.com' 

    urls = get_paths(rooturl)
    start_download(s3url, urls)