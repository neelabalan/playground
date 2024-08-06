import asyncio
import collections
import json
import time

import aiohttp


async def fetch(session: aiohttp.ClientSession, url: str) -> dict[str, str]:
    observation = {}
    try:
        async with session.get(url.strip(), timeout=10) as response:
            observation = {'url': url, 'status_code': str(response.status)}
    except asyncio.TimeoutError:
        observation = {'status_code': 'timeout', 'url': url}
    except Exception as ex:
        observation = {'status_code': 'errored_out', 'url': url}
        print(ex)
    return observation


async def get_all(links: list[str], number_of_concurrent_req: int) -> list[dict[str, str]]:
    data = []
    async with aiohttp.ClientSession() as session:
        tasks = []
        # max number of concurrent requests
        semaphore = asyncio.Semaphore(number_of_concurrent_req)

        async def sem_fetch(url):
            async with semaphore:
                return await fetch(session, url)

        for url in links:
            tasks.append(sem_fetch(url))

        data = await asyncio.gather(*tasks)
    return data


async def run_async(number_of_concurrent_req: int):
    with open('data/links.txt') as _file:
        links = _file.readlines()

    start_time = time.time()
    data = await get_all(links, number_of_concurrent_req=number_of_concurrent_req)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f'\nTotal execution time: {execution_time:.2f} seconds')

    data = sorted(data, key=lambda x: x['url'])
    ordered_list = []
    for dat in data:
        ordered_list.append(collections.OrderedDict({'url': dat['url'].strip(), 'status_code': dat['status_code']}))

    with open('results/response_python_async.json', 'w') as _file:
        json.dump(ordered_list, _file, indent=4)
        print('file serialized')
