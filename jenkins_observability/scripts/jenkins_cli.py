#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx>=0.28.1",
#     "pandas>=2.3.2",
#     "pyarrow==17.0.0",
# ]
# ///


# uv run jenkins_cli.py
import argparse
import asyncio
import datetime
import json
import pathlib
import time

import httpx
import pandas as pd


class JenkinsClient:
    def __init__(self, base_url: str, username: str, token: str | None = None, password: str | None = None):
        self.base_url: str = base_url.rstrip('/')

        if token:
            self.auth: httpx.BasicAuth = httpx.BasicAuth(username, token)
        elif password:
            self.auth: httpx.BasicAuth = httpx.BasicAuth(username, password)
        else:
            raise ValueError('Either token or password must be provided')

        self.headers: dict[str, str] = {'Accept': 'application/json'}
        self.timeout: httpx.Timeout = httpx.Timeout(30.0)
        self._client: httpx.AsyncClient | None = None
        self._crumb: dict[str, str] | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(auth=self.auth, headers=self.headers, timeout=self.timeout)
        await self._get_crumb()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _get_crumb(self):
        assert self._client is not None
        try:
            response = await self._client.get(f'{self.base_url}/crumbIssuer/api/json')
            if response.status_code == 200:
                crumb_data = response.json()
                self._crumb = {
                    'name': crumb_data.get('crumbRequestField', 'Jenkins-Crumb'),
                    'value': crumb_data.get('crumb', ''),
                }
                print(f'retrieved CSRF crumb: {self._crumb["name"]}')
            else:
                print('CSRF protection not enabled or crumb not available')
                self._crumb = None
        except Exception as e:
            print(f'could not retrieve CSRF crumb: {e}')
            self._crumb = None

    async def get(self, path: str, params: dict | None = None) -> httpx.Response:
        assert self._client is not None
        url = f'{self.base_url}/{path.strip("/")}'
        return await self._client.get(url, params=params)

    async def post(self, path: str, data: dict | None = None, json_data: dict | None = None) -> httpx.Response:
        assert self._client is not None
        url = f'{self.base_url}/{path.strip("/")}'
        headers = {}
        if self._crumb:
            headers[self._crumb['name']] = self._crumb['value']
        return await self._client.post(url, data=data, json=json_data, headers=headers)


class JenkinsBuildExporter:
    def __init__(self, jenkins_client: JenkinsClient, max_workers: int = 5):
        self.jenkins_client: JenkinsClient = jenkins_client
        self.max_workers: int = max_workers

    async def _get_build_numbers(
        self, pipeline_path: str, page_size: int | None = None, start_offset: int = 0
    ) -> list[int]:
        if page_size:
            end_offset = start_offset + page_size
            params = {'tree': f'allBuilds[number]{{{start_offset},{end_offset}}}'}
        else:
            params = {'tree': 'allBuilds[number]'}

        try:
            response = await self.jenkins_client.get(f'{pipeline_path}/api/json', params=params)
            response.raise_for_status()
            data = response.json()
            return [build['number'] for build in data.get('allBuilds', [])]
        except httpx.HTTPError as e:
            print(f'error fetching build numbers for {pipeline_path}: {e}')
            return []

    async def _get_build_detail(self, pipeline_path: str, build_number: int) -> dict | None:
        try:
            response = await self.jenkins_client.get(f'{pipeline_path}/{build_number}/api/json')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f'error fetching build {build_number} for {pipeline_path}: {e}')
            return None

    def _extract_queue_wait_time(self, build_detail: dict) -> int | None:
        for action in build_detail.get('actions', []):
            if action.get('_class') == 'jenkins.metrics.impl.TimeInQueueAction':
                return (
                    action.get('blockedTimeMillis', 0)
                    + action.get('buildableTimeMillis', 0)
                    + action.get('waitingTimeMillis', 0)
                )
        return None

    def _extract_execution_time(self, build_detail: dict) -> int | None:
        for action in build_detail.get('actions', []):
            if action.get('_class') == 'jenkins.metrics.impl.TimeInQueueAction':
                return action.get('executingTimeMillis')
        return None

    def _extract_triggered_by(self, build_detail: dict) -> str | None:
        for action in build_detail.get('actions', []):
            if action.get('_class') == 'hudson.model.CauseAction':
                causes = action.get('causes', [])
                if causes:
                    cause = causes[0]
                    return cause.get('userName') or cause.get('userId')
        return None

    def _extract_build_data(self, pipeline_path: str, build_detail: dict) -> dict:
        timestamp_ms = build_detail.get('timestamp', 0)
        duration_ms = build_detail.get('duration', 0)
        estimated_duration_ms = build_detail.get('estimatedDuration', 0)

        start_time = datetime.datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else None
        end_time = (
            datetime.datetime.fromtimestamp((timestamp_ms + duration_ms) / 1000)
            if timestamp_ms and duration_ms
            else None
        )

        status = build_detail.get('result', 'unknown').lower()

        queue_wait_time_ms = self._extract_queue_wait_time(build_detail)
        executing_time_ms = self._extract_execution_time(build_detail)
        triggered_by = self._extract_triggered_by(build_detail)

        return {
            'pipeline_name': pipeline_path,
            'build_number': build_detail.get('number'),
            'build_start_time': start_time,
            'build_end_time': end_time,
            'status': status,
            'execution_time': executing_time_ms / 1000.0 if executing_time_ms else None,
            'estimated_duration': estimated_duration_ms / 1000.0 if estimated_duration_ms else None,
            'queue_wait_time': queue_wait_time_ms / 1000.0 if queue_wait_time_ms else None,
            'url': build_detail.get('url'),
            'triggered_by': triggered_by,
        }

    async def _fetch_pipeline_data(self, pipeline_path: str, page_size: int | None = None) -> list[dict]:
        print(f'fetching builds for pipeline: {pipeline_path}')

        if page_size:
            all_builds = []
            start_offset = 0

            while True:
                build_numbers = await self._get_build_numbers(pipeline_path, page_size, start_offset)
                if not build_numbers:
                    break

                print(f'fetched page with {len(build_numbers)} builds (offset {start_offset})')

                semaphore = asyncio.Semaphore(self.max_workers)

                async def fetch_with_semaphore(build_number: int) -> dict | None:
                    async with semaphore:
                        build_detail = await self._get_build_detail(pipeline_path, build_number)
                        if build_detail:
                            return self._extract_build_data(pipeline_path, build_detail)
                        return None

                tasks = [fetch_with_semaphore(num) for num in build_numbers]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                page_data = []
                for result in results:
                    if isinstance(result, dict):
                        page_data.append(result)
                    elif isinstance(result, Exception):
                        print(f'error processing build: {result}')

                all_builds.extend(page_data)
                print(f'processed {len(page_data)} builds from page (total: {len(all_builds)})')

                if len(build_numbers) < page_size:
                    break

                start_offset += page_size

            print(f'successfully fetched {len(all_builds)} builds for {pipeline_path}')
            return all_builds
        else:
            build_numbers = await self._get_build_numbers(pipeline_path)
            if not build_numbers:
                print(f'no builds found for {pipeline_path}')
                return []

            print(f'found {len(build_numbers)} builds for {pipeline_path}')

            semaphore = asyncio.Semaphore(self.max_workers)

            async def fetch_with_semaphore(build_number: int) -> dict | None:
                async with semaphore:
                    build_detail = await self._get_build_detail(pipeline_path, build_number)
                    if build_detail:
                        return self._extract_build_data(pipeline_path, build_detail)
                    return None

            tasks = [fetch_with_semaphore(num) for num in build_numbers]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            pipeline_data = []
            for result in results:
                if isinstance(result, dict):
                    pipeline_data.append(result)
                elif isinstance(result, Exception):
                    print(f'error processing build: {result}')

            print(f'successfully fetched {len(pipeline_data)} builds for {pipeline_path}')
            return pipeline_data

    async def export_pipeline_builds(
        self, pipeline_path: str, output_path: str | pathlib.Path, page_size: int | None = None
    ) -> None:
        output_path = pathlib.Path(output_path)
        output_path.mkdir(exist_ok=True)

        pipeline_data = await self._fetch_pipeline_data(pipeline_path, page_size)
        if pipeline_data:
            df = pd.DataFrame(pipeline_data)
            safe_name = pipeline_path.replace('/', '_').replace(' ', '_')
            file_path = output_path / f'{safe_name}_builds.parquet'
            df.to_parquet(file_path, index=False)
            print(f'exported {len(pipeline_data)} records for {pipeline_path} to {file_path}')


async def trigger_job(jenkins_client: JenkinsClient, job_name: str) -> bool:
    try:
        print(f'triggering job: {job_name}')
        response = await jenkins_client.post(f'job/{job_name}/build')
        response.raise_for_status()

        location = response.headers.get('Location')
        if location and '/queue/item/' in location:
            queue_id = location.split('/queue/item/')[1].rstrip('/')
            print(f'job {job_name} queued successfully (queue ID: {queue_id})')
        else:
            print(f'job {job_name} triggered successfully')

        return True
    except httpx.HTTPError as e:
        print(f'error triggering job {job_name}: {e}')
        return False


async def list_job_builds(jenkins_client: JenkinsClient, job_name: str) -> list[int]:
    try:
        response = await jenkins_client.get(f'job/{job_name}/api/json', params={'tree': 'builds[number]'})
        response.raise_for_status()
        builds = response.json().get('builds', [])
        return [build['number'] for build in builds]
    except httpx.HTTPError as e:
        print(f'error listing builds for {job_name}: {e}')
        return []


def load_config(config_path: pathlib.Path) -> dict:
    with open(config_path) as f:
        return json.load(f)


async def export_command(args):
    config = load_config(pathlib.Path(args.config))

    async with JenkinsClient(
        config['base_url'], config['username'], token=config.get('token'), password=config.get('password')
    ) as jenkins_client:
        exporter = JenkinsBuildExporter(jenkins_client, args.workers)

        for pipeline_path in config['pipelines']:
            try:
                page_size = getattr(args, 'page_size', None)
                await exporter.export_pipeline_builds(pipeline_path, args.output, page_size)
            except Exception as e:
                print(f'error processing pipeline {pipeline_path}: {e}')

    print('export completed!')


async def execute_job_schedule(args):
    config = load_config(pathlib.Path(args.config))

    job_trigger_counts = {
        'ecgo_docker': 23,
        'file_operations': 17,
        'hello_world': 31,
        'parallel_pipeline': 14,
        'system_info': 28,
        'test1_pipeline': 19,
        'test2_pipeline': 25,
        'test3_pipeline': 12,
    }

    async with JenkinsClient(
        config['base_url'], config['username'], token=config.get('token'), password=config.get('password')
    ) as jenkins_client:
        total_triggered = 0
        total_queued = 0

        for pipeline_path in config['pipelines']:
            job_name = pipeline_path.replace('job/', '')

            if job_name in job_trigger_counts:
                trigger_count = job_trigger_counts[job_name]
                print(f'triggering {trigger_count} builds for job: {job_name}')

                job_triggered = 0
                job_queued = 0

                for i in range(trigger_count):
                    print(f'triggering build {i + 1}/{trigger_count} for {job_name}...')
                    success = await trigger_job(jenkins_client, job_name)
                    if success:
                        job_queued += 1
                        total_queued += 1
                    job_triggered += 1
                    total_triggered += 1
                    if i < trigger_count - 1:
                        print('waiting 1 second before next trigger...')
                        time.sleep(1)
                print(f'job {job_name}: {job_queued}/{job_triggered} builds successfully queued')
                print('waiting 2 seconds before next job...')
                time.sleep(2)

        print('job schedule execution completed!')
        print(f'total builds triggered: {total_triggered}')
        print(f'total builds queued: {total_queued}')
        print(
            f'success rate: {(total_queued / total_triggered) * 100:.1f}%'
            if total_triggered > 0
            else 'no builds triggered'
        )


async def list_command(args):
    config = load_config(pathlib.Path(args.config))

    async with JenkinsClient(
        config['base_url'], config['username'], token=config.get('token'), password=config.get('password')
    ) as jenkins_client:
        if args.job:
            builds = await list_job_builds(jenkins_client, args.job)
            print(f"builds for job '{args.job}':")
            for build_num in builds:
                print(f'  build number: {build_num}')
        else:
            for pipeline_path in config['pipelines']:
                job_name = pipeline_path.replace('job/', '')
                builds = await list_job_builds(jenkins_client, job_name)
                print(f"builds for job '{job_name}': {len(builds)} builds")


async def main():
    parser = argparse.ArgumentParser(description='jenkins management tool')
    subparsers = parser.add_subparsers(dest='command', help='available commands')

    export_parser = subparsers.add_parser('export', help='export build data to parquet files')
    export_parser.add_argument('--config', required=True, help='path to jenkins configuration file')
    export_parser.add_argument('--output', default='jenkins_build_data', help='output directory')
    export_parser.add_argument('--workers', type=int, default=5, help='maximum number of concurrent workers')
    export_parser.add_argument(
        '--page-size', default=100, type=int, help='number of builds to fetch per page for pagination'
    )

    trigger_parser = subparsers.add_parser('trigger', help='trigger jenkins jobs')
    trigger_parser.add_argument('--config', required=True, help='path to jenkins configuration file')

    list_parser = subparsers.add_parser('list', help='list jenkins builds')
    list_parser.add_argument('--config', required=True, help='path to jenkins configuration file')
    list_parser.add_argument('--job', help='specific job to list builds for (if not provided, lists all jobs in config)')

    args = parser.parse_args()

    if args.command == 'export':
        await export_command(args)
    elif args.command == 'trigger':
        await execute_job_schedule(args)
    elif args.command == 'list':
        await list_command(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
