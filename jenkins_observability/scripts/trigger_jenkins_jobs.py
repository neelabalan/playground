import typing

import httpx

config: dict[str, typing.Any] = {
    'username': 'jenkins',
    'token': '1157c7bda4b9b32aeef77b7fa934ee0e26',
    'base_url': 'http://localhost:8080/',
    'pipelines': [
        'job/ecgo_docker',
        'job/file_operations/',
        'job/hello_world',
        'job/parallel_pipeline',
        'job/system_info',
        'job/test1_pipeline',
        'job/test2_pipeline',
        'job/test3_pipeline',
    ],
}


def trigger_job(job_name: str) -> None:
    url = f'{config["base_url"]}job/{job_name}/build'
    print(f'triggered {job_name}')
    with httpx.Client(auth=(config['username'], config['token'])) as client:
        response = client.post(url)
        response.raise_for_status()


if __name__ == '__main__':
    for job in config['pipelines']:
        trigger_job(job)
