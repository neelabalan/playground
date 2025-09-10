#!/usr/bin/env python3

import argparse
import asyncio
import datetime
import json
import pathlib

import httpx
import pandas as pd


class JenkinsClient:
    def __init__(self, base_url: str, username: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.auth = httpx.BasicAuth(username, token)
        self.headers = {'Accept': 'application/json'}
        self.timeout = httpx.Timeout(30.0)
        self._client = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(auth=self.auth, headers=self.headers, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def get(self, path: str, params: dict = None) -> httpx.Response:
        url = f'{self.base_url}/{path.strip("/")}'
        return await self._client.get(url, params=params)

    async def post(self, path: str, data: dict = None, json_data: dict = None) -> httpx.Response:
        url = f'{self.base_url}/{path.strip("/")}'
        return await self._client.post(url, data=data, json=json_data)


class JenkinsBuildExporter:
    def __init__(self, jenkins_client: JenkinsClient, max_workers: int = 5):
        self.jenkins_client = jenkins_client
        self.max_workers = max_workers

    async def _get_build_numbers(self, pipeline_path: str) -> list[int]:
        params = {'tree': 'builds[number]'}

        try:
            response = await self.jenkins_client.get(f'{pipeline_path}/api/json', params=params)
            response.raise_for_status()
            data = response.json()
            return [build['number'] for build in data.get('builds', [])]
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

    def _extract_build_data(self, pipeline_path: str, build_detail: dict) -> dict:
        timestamp_ms = build_detail.get('timestamp', 0)
        duration_ms = build_detail.get('duration', 0)
        estimated_duration_ms = build_detail.get('estimatedDuration', 0)

        start_time = datetime.datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else None
        end_time = datetime.datetime.fromtimestamp((timestamp_ms + duration_ms) / 1000) if timestamp_ms and duration_ms else None

        status = build_detail.get('result', 'unknown').lower()

        return {
            'pipeline_name': pipeline_path,
            'build_number': build_detail.get('number'),
            'build_start_time': start_time,
            'build_end_time': end_time,
            'status': status,
            'total_duration': duration_ms / 1000.0,
            'duration_ms': duration_ms,
            'timestamp_ms': timestamp_ms,
            'url': build_detail.get('url'),
            'building': build_detail.get('building', False),
            'queue_id': build_detail.get('queueId'),
            'estimated_duration': estimated_duration_ms / 1000.0 if estimated_duration_ms else None,
        }

    async def _fetch_pipeline_data(self, pipeline_path: str) -> list[dict]:
        print(f'fetching builds for pipeline: {pipeline_path}')

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

    async def export_pipeline_builds(self, pipeline_path: str, output_path: str | pathlib.Path) -> None:
        output_path = pathlib.Path(output_path)
        output_path.mkdir(exist_ok=True)

        pipeline_data = await self._fetch_pipeline_data(pipeline_path)
        if pipeline_data:
            df = pd.DataFrame(pipeline_data)
            safe_name = pipeline_path.replace('/', '_').replace(' ', '_')
            file_path = output_path / f'{safe_name}_builds.parquet'
            df.to_parquet(file_path, index=False)
            print(f'exported {len(pipeline_data)} records for {pipeline_path} to {file_path}')


def load_config(config_path: pathlib.Path) -> dict:
    with open(config_path) as f:
        return json.load(f)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Path to Jenkins configuration file')
    parser.add_argument('--output', default='jenkins_build_data', help='Output directory')
    parser.add_argument('--workers', type=int, default=5, help='Maximum number of concurrent workers (default: 5)')
    args = parser.parse_args()

    config_path = pathlib.Path(args.config)
    if not config_path.exists():
        print(f'config file not found: {config_path}')
        return 1

    config = load_config(config_path)

    async with JenkinsClient(config['base_url'], config['username'], config['token']) as jenkins_client:
        exporter = JenkinsBuildExporter(jenkins_client, args.workers)

        for pipeline_path in config['pipelines']:
            try:
                await exporter.export_pipeline_builds(pipeline_path, args.output)
            except Exception as e:
                print(f'error processing pipeline {pipeline_path}: {e}')

    print('export completed!')


if __name__ == '__main__':
    asyncio.run(main())
