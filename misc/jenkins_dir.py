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

    return httpx.AsyncClient(headers=headers, verify=verify_ssl, timeout=timeout, follow_redirects=True)


def validate_jenkins_url(url: str) -> str:
    parsed = urlp.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f'Invalid Jenkins URL: {url}')

    if not url.endswith('/'):
        url += '/'

    return url


async def test_jenkins_connection(client: httpx.AsyncClient, jenkins_url: str) -> None:
    try:
        response = await client.get(urlp.urljoin(jenkins_url, 'api/json'))
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


async def fetch_jenkins_jobs(client: httpx.AsyncClient, jenkins_url: str, path: str = '') -> list[dict[str, typing.Any]]:
    api_url = urlp.urljoin(jenkins_url, f'{path}api/json?tree=jobs[name,_class,color]')

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


async def traverse_jenkins_structure(
    client: httpx.AsyncClient, jenkins_url: str, path: str = ''
) -> dict[str, typing.Any] | list[dict[str, typing.Any]]:
    jobs = await fetch_jenkins_jobs(client, jenkins_url, path)

    result = {}
    pipelines = []

    for job in jobs:
        job_name = job.get('name', '')
        job_class = job.get('_class', '')

        if 'Folder' in job_class or 'OrganizationFolder' in job_class:
            job_path = f'{path}job/{job_name}/'
            subdirs = await traverse_jenkins_structure(client, jenkins_url, job_path)
            result[job_name] = subdirs
        else:
            job_url = urlp.urljoin(jenkins_url, f'{path}job/{job_name}/')
            pipelines.append({'name': job_name, 'url': job_url})

    if pipelines:
        if result:
            result['pipelines'] = pipelines
        else:
            return pipelines

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
  python jenkins_dir.py --jenkins-url=https://jenkins.example.com --output=output.json
        """,
    )
    parser.add_argument('--jenkins_url', help='Jenkins server URL')
    parser.add_argument('--output', default='output.json', help='Output JSON file name')
    parser.add_argument('--username', help='Jenkins username (overrides env var)')
    parser.add_argument('--token', help='Jenkins API token (overrides env var)')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Disable SSL certificate verification')
    parser.add_argument('--timeout', type=float, default=30.0, help='Request timeout in seconds (default: 30)')

    args = parser.parse_args()

    try:
        jenkins_url = validate_jenkins_url(args.jenkins_url)

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

        print(f'Connecting to Jenkins at {jenkins_url}')
        print(f'Username: {username}')

        async with await create_authenticated_client(
            username=username, token=token, verify_ssl=not args.no_ssl_verify, timeout=args.timeout
        ) as client:
            await test_jenkins_connection(client, jenkins_url)
            print('Connection successful!')

            print('Fetching Jenkins job structure...')
            jenkins_structure = await traverse_jenkins_structure(client, jenkins_url)

            print(f'Writing results to {args.output_file}')
            with open(args.output_file, 'w') as f:
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


if __name__ == '__main__':
    asyncio.run(main())
