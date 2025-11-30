import collections
import json
import time

import requests


def fetch(url: str) -> str:
    status_code = None
    try:
        response = requests.get(url.strip(), timeout=2)
        status_code = str(response.status_code)
    except requests.Timeout:
        status_code = 'timeout'
    except Exception as ex:
        status_code = 'errored_out'
    return status_code


def get_all(links: list[str]) -> list[dict[str, str]]:
    data = []
    for count, url in enumerate(links):
        result = fetch(url)
        data.append({'url': url, 'status_code': result})
        print(f'{count + 1}={url}')
    return data


def run_seq():
    with open('data/links.txt') as _file:
        links = _file.readlines()

    start_time = time.time()
    data = get_all(links)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f'\nTotal execution time: {execution_time:.2f} seconds')

    data = sorted(data, key=lambda x: x['url'])
    ordered_list = []
    for dat in data:
        ordered_list.append(collections.OrderedDict({'url': dat['url'].strip(), 'status_code': dat['status_code']}))
    with open('results/response_python_sync.json', 'w') as _file:
        json.dump(ordered_list, _file, indent=4)
        print('file serialized')
