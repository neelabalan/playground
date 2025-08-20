import argparse
import asyncio
import base64
import json
import os
import sys
import typing
import urllib.parse as urlp

import httpx


class JenkinsAPIError(Exception):
    pass


async def create_authenticated_client(
    username: str | None = None, token: str | None = None, verify_ssl: bool = True, timeout: float = 30.0
) -> httpx.AsyncClient:
    headers = {}

    if username and token:
        auth_string = f'{username}:{token}'
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        headers['Authorization'] = f'Basic {encoded_auth}'

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)

    return httpx.AsyncClient(headers=headers, verify=verify_ssl, timeout=timeout, follow_redirects=True, limits=limits)


def validate_jenkins_url(url: str) -> str:
    parsed = urlp.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f'Invalid Jenkins URL: {url}')

    if not url.endswith('/'):
        url += '/'

    return url


async def test_jenkins_connection(client: httpx.AsyncClient, url: str) -> None:
    try:
        response = await client.get(urlp.urljoin(url, 'api/json'))
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise JenkinsAPIError('Authentication failed. Check username and token.')
        elif e.response.status_code == 403:
            raise JenkinsAPIError('Access forbidden. Check permissions.')
        else:
            raise JenkinsAPIError(f'HTTP error {e.response.status_code}: {e.response.text}')
    except httpx.RequestError as e:
        raise JenkinsAPIError(f'Connection error: {e}')


async def fetch_jenkins_jobs(client: httpx.AsyncClient, url: str, path: str = '') -> list[dict[str, typing.Any]]:
    api_url = urlp.urljoin(url, f'{path}api/json?tree=jobs[name,_class,color]')

    try:
        response = await client.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data.get('jobs', [])
    except httpx.HTTPStatusError as e:
        print(f'HTTP error fetching {api_url}: {e.response.status_code}', file=sys.stderr)
        return []
    except httpx.RequestError as e:
        print(f'Request error fetching {api_url}: {e}', file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f'JSON decode error for {api_url}: {e}', file=sys.stderr)
        return []


async def fetch_job_script_path(
    client: httpx.AsyncClient, url: str, job_path: str, job_name: str, semaphore: asyncio.Semaphore
) -> str | None:
    async with semaphore:
        config_url = urlp.urljoin(url, f'{job_path}job/{job_name}/config.xml')

        try:
            response = await client.get(config_url)
            response.raise_for_status()
            config_xml = response.text

            import xml.etree.ElementTree as ET

            root = ET.fromstring(config_xml)

            script_path_elem = root.find('.//scriptPath')
            if script_path_elem is not None and script_path_elem.text:
                return script_path_elem.text.strip()

            definition_elem = root.find('.//definition')
            if definition_elem is not None:
                script_path_elem = definition_elem.find('.//scriptPath')
                if script_path_elem is not None and script_path_elem.text:
                    return script_path_elem.text.strip()

            return None
        except Exception:
            return None


async def process_pipeline_job(
    client: httpx.AsyncClient, url: str, path: str, job_name: str, semaphore: asyncio.Semaphore
) -> dict[str, typing.Any]:
    print(f'Processing pipeline: {job_name}')
    job_url = urlp.urljoin(url, f'{path}job/{job_name}/')
    script_path = await fetch_job_script_path(client, url, path, job_name, semaphore)

    pipeline_info = {'name': job_name, 'url': job_url}

    if script_path:
        pipeline_info['script_path'] = script_path
        print(f'  Found script path for {job_name}: {script_path}')
    else:
        print(f'  No script path found for {job_name}')

    return pipeline_info


async def traverse_jenkins_structure(
    client: httpx.AsyncClient, url: str, path: str = '', max_concurrent: int = 10
) -> dict[str, typing.Any] | list[dict[str, typing.Any]]:
    current_path = path if path else 'root'
    print(f'Fetching jobs from: {current_path}')
    jobs = await fetch_jenkins_jobs(client, url, path)
    print(f'Found {len(jobs)} items in {current_path}')

    result = {}
    pipeline_jobs = []
    folder_tasks = []

    semaphore = asyncio.Semaphore(max_concurrent)

    for job in jobs:
        job_name = job.get('name', '')
        job_class = job.get('_class', '')

        if 'Folder' in job_class or 'OrganizationFolder' in job_class:
            print(f'Scheduling folder processing: {job_name}')
            job_path = f'{path}job/{job_name}/'
            folder_task = traverse_jenkins_structure(client, url, job_path, max_concurrent)
            folder_tasks.append((job_name, folder_task))
        else:
            pipeline_jobs.append((job_name, job))

    print(f'Processing {len(folder_tasks)} folders concurrently')
    if folder_tasks:
        folder_results = await asyncio.gather(*[task for _, task in folder_tasks], return_exceptions=True)
        for (folder_name, _), folder_result in zip(folder_tasks, folder_results):
            if isinstance(folder_result, Exception):
                print(f'Error processing folder {folder_name}: {folder_result}')
                result[folder_name] = {}
            else:
                result[folder_name] = folder_result
                print(f'Completed folder: {folder_name}')

    print(f'Processing {len(pipeline_jobs)} pipelines concurrently')
    if pipeline_jobs:
        pipeline_tasks = [process_pipeline_job(client, url, path, job_name, semaphore) for job_name, _ in pipeline_jobs]
        pipelines = await asyncio.gather(*pipeline_tasks, return_exceptions=True)

        valid_pipelines = []
        for pipeline in pipelines:
            if isinstance(pipeline, Exception):
                print(f'Error processing pipeline: {pipeline}')
            else:
                valid_pipelines.append(pipeline)

        if valid_pipelines:
            print(f'  Adding {len(valid_pipelines)} pipelines')
            if result:
                result['pipelines'] = valid_pipelines
            else:
                return valid_pipelines

    print(f'Completed processing {current_path}')
    return result


def get_credentials() -> tuple[str | None, str | None]:
    username = os.getenv('JENKINS_USERNAME')
    token = os.getenv('JENKINS_TOKEN') or os.getenv('JENKINS_PASSWORD')

    return username, token


async def main() -> None:
    parser = argparse.ArgumentParser(
        description='Extract Jenkins job structure via API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Authentication:
  Set environment variables:
    JENKINS_USERNAME - Jenkins username
    JENKINS_TOKEN - Jenkins API token (recommended) or password

Examples:
  export JENKINS_USERNAME=myuser
  export JENKINS_TOKEN=abc123def456
  python jenkins_dir.py --url=https://jenkins.example.com
        """,
    )
    parser.add_argument('--url', help='Jenkins server URL')
    parser.add_argument('--output', default='output.json', help='Output JSON file name')
    parser.add_argument('--username', help='Jenkins username (overrides env var)')
    parser.add_argument('--token', help='Jenkins API token (overrides env var)')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Disable SSL certificate verification')
    parser.add_argument('--timeout', type=float, default=30.0, help='Request timeout in seconds (default: 30)')
    parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent requests (default: 10)')

    args = parser.parse_args()

    try:
        url = validate_jenkins_url(args.url)

        username = args.username
        token = args.token

        if not username or not token:
            env_username, env_token = get_credentials()
            username = username or env_username
            token = token or env_token

        if not username or not token:
            print('Error: Jenkins credentials required.', file=sys.stderr)
            print('Set JENKINS_USERNAME and JENKINS_TOKEN environment variables', file=sys.stderr)
            print('or use --username and --token arguments.', file=sys.stderr)
            sys.exit(1)

        print(f'Connecting to Jenkins at {url}')
        print(f'Username: {username}')

        async with await create_authenticated_client(
            username=username, token=token, verify_ssl=not args.no_ssl_verify, timeout=args.timeout
        ) as client:
            await test_jenkins_connection(client, url)
            print('Connection successful!')

            print('Starting Jenkins job structure traversal...')
            jenkins_structure = await traverse_jenkins_structure(client, url, max_concurrent=args.max_concurrent)
            print('Completed Jenkins job structure traversal')

            print(f'Writing results to {args.output}')
            with open(args.output, 'w') as f:
                json.dump(jenkins_structure, f, indent=2)

            print('Done!')

    except JenkinsAPIError as e:
        print(f'Jenkins API Error: {e}', file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f'Configuration Error: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Unexpected Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
