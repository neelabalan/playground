#!/usr/bin/env python3
# /// script
# dependencies = [
#     "httpx==0.28.1",
#     "pandas==2.3.2",
#     "opentelemetry-api==1.28.2",
#     "opentelemetry-sdk==1.28.2",
#     "opentelemetry-exporter-otlp==1.28.2"
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
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class JenkinsClient:
    def __init__(self, base_url: str, username: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.auth = httpx.BasicAuth(username, token)
        self.headers = {'Accept': 'application/json'}
        self.timeout = httpx.Timeout(30.0)
        self._client = None
        self._crumb = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(auth=self.auth, headers=self.headers, timeout=self.timeout)
        await self._get_crumb()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _get_crumb(self):
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

    async def get(self, path: str, params: dict = None) -> httpx.Response:
        url = f'{self.base_url}/{path.strip("/")}'
        return await self._client.get(url, params=params)

    async def post(self, path: str, data: dict = None, json_data: dict = None) -> httpx.Response:
        url = f'{self.base_url}/{path.strip("/")}'
        headers = {}
        if self._crumb:
            headers[self._crumb['name']] = self._crumb['value']
        return await self._client.post(url, data=data, json=json_data, headers=headers)


class JenkinsBuildFetcher:
    def __init__(self, jenkins_client: JenkinsClient):
        self.jenkins_client = jenkins_client

    async def get_job_builds(self, job_path: str) -> list[dict]:
        try:
            response = await self.jenkins_client.get(
                f'{job_path}/api/json', params={'tree': 'builds[number,timestamp,duration,result,url,building]'}
            )
            response.raise_for_status()
            data = response.json()
            return data.get('builds', [])
        except httpx.HTTPError as e:
            print(f'error fetching builds for {job_path}: {e}')
            return []

    async def get_build_steps(self, job_path: str, build_number: int) -> list[dict]:
        is_pipeline = await self.is_pipeline_job(job_path)
        if not is_pipeline:
            print(f'skipping workflow steps for {job_path}/{build_number} (not a Pipeline job)')
            return [{
                'stage_name': 'build',
                'stage_id': 'build',
                'start_time': 0,
                'duration': 0,
                'status': 'COMPLETED',
                'steps': [{
                    'step_name': 'build',
                    'step_id': 'build',
                    'start_time': 0,
                    'duration': 0,
                    'status': 'COMPLETED',
                    'type': 'BUILD'
                }]
            }]

        try:
            workflow_run_url = f'{job_path}/{build_number}/wfapi/describe'
            response = await self.jenkins_client.get(workflow_run_url)
            response.raise_for_status()
            workflow_data = response.json()

            steps = []
            for stage in workflow_data.get('stages', []):
                stage_steps = {
                    'stage_name': stage.get('name', 'unknown'),
                    'stage_id': stage.get('id'),
                    'start_time': stage.get('startTimeMillis', 0),
                    'duration': stage.get('durationMillis', 0),
                    'status': stage.get('status', 'UNKNOWN'),
                    'steps': [],
                }

                for step_flow in stage.get('stageFlowNodes', []):
                    step_info = {
                        'step_name': step_flow.get('name', 'unknown'),
                        'step_id': step_flow.get('id'),
                        'start_time': step_flow.get('startTimeMillis', 0),
                        'duration': step_flow.get('durationMillis', 0),
                        'status': step_flow.get('status', 'UNKNOWN'),
                        'type': step_flow.get('type', 'STEP'),
                    }
                    stage_steps['steps'].append(step_info)

                steps.append(stage_steps)

            return steps
        except httpx.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 404:
                    print(f'workflow API not available for {job_path}/{build_number} (build may not have workflow data)')
                    # Return a basic stage for builds without workflow data
                    return [{
                        'stage_name': 'build',
                        'stage_id': 'build',
                        'start_time': 0,
                        'duration': 0,
                        'status': 'COMPLETED',
                        'steps': [{
                            'step_name': 'build',
                            'step_id': 'build',
                            'start_time': 0,
                            'duration': 0,
                            'status': 'COMPLETED',
                            'type': 'BUILD'
                        }]
                    }]
                else:
                    print(f'HTTP error fetching build steps for {job_path}/{build_number}: {e.response.status_code}')
                    return []
            else:
                print(f'error fetching build steps for {job_path}/{build_number}: {e}')
                return []
        except Exception as e:
            print(f'unexpected error fetching build steps for {job_path}/{build_number}: {e}')
            return []

    async def is_pipeline_job(self, job_path: str) -> bool:
        """Check if a job is a Pipeline job by examining its class type"""
        try:
            response = await self.jenkins_client.get(f'{job_path}/api/json', params={'tree': '_class'})
            response.raise_for_status()
            data = response.json()
            job_class = data.get('_class', '')
            return 'WorkflowJob' in job_class or 'org.jenkinsci.plugins.workflow' in job_class
        except httpx.HTTPError as e:
            print(f'error checking job type for {job_path}: {e}')
            return False


class TracePublisher:
    def __init__(self, tempo_endpoint: str):
        trace.set_tracer_provider(TracerProvider())
        if not tempo_endpoint.endswith('/v1/traces'):
            tempo_endpoint = tempo_endpoint.rstrip('/') + '/v1/traces'
        exporter = OTLPSpanExporter(
            endpoint=tempo_endpoint,
            headers={},
            timeout=30.0
        )
        span_processor = BatchSpanProcessor(exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        self.tracer = trace.get_tracer('jenkins-observability')
        self.span_processor = span_processor
        self.exporter = exporter

    def publish_build_trace_with_steps(self, job_name: str, build_data: dict, steps_data: list[dict], tempo_endpoint: str = None):
        print(f'Creating trace for {job_name} build {build_data["number"]}')

        build_start_time = datetime.datetime.fromtimestamp(build_data['timestamp'] / 1000.0)
        build_duration_ms = build_data.get('duration', 0)
        build_end_time = build_start_time + datetime.timedelta(milliseconds=build_duration_ms)

        # Convert to nanoseconds for OpenTelemetry
        build_start_ns = int(build_start_time.timestamp() * 1_000_000_000)
        build_end_ns = int(build_end_time.timestamp() * 1_000_000_000)

        with self.tracer.start_as_current_span(
            name=f'{job_name}-build-{build_data["number"]}',
            start_time=build_start_ns,
        ) as build_span:
            build_span.set_attribute('jenkins.job', job_name)
            build_span.set_attribute('jenkins.build_number', build_data['number'])
            build_span.set_attribute('jenkins.url', build_data['url'])
            build_span.set_attribute('jenkins.result', build_data.get('result', 'UNKNOWN'))
            build_span.set_attribute('jenkins.duration_ms', build_duration_ms)
            build_span.set_attribute('jenkins.type', 'build')
            build_span.set_attribute('service.name', 'jenkins-observability')

            for stage_data in steps_data:
                stage_start_time = (
                    datetime.datetime.fromtimestamp(stage_data['start_time'] / 1000.0)
                    if stage_data['start_time']
                    else build_start_time
                )
                stage_duration_ms = stage_data.get('duration', 0)
                stage_end_time = stage_start_time + datetime.timedelta(milliseconds=stage_duration_ms)

                # Convert to nanoseconds for OpenTelemetry
                stage_start_ns = int(stage_start_time.timestamp() * 1_000_000_000)
                stage_end_ns = int(stage_end_time.timestamp() * 1_000_000_000)

                with self.tracer.start_as_current_span(
                    name=f'{stage_data["stage_name"]}',
                    start_time=stage_start_ns,
                ) as stage_span:
                    stage_span.set_attribute('jenkins.job', job_name)
                    stage_span.set_attribute('jenkins.build_number', build_data['number'])
                    stage_span.set_attribute('jenkins.stage_name', stage_data['stage_name'])
                    stage_span.set_attribute('jenkins.stage_id', stage_data.get('stage_id', ''))
                    stage_span.set_attribute('jenkins.status', stage_data.get('status', 'UNKNOWN'))
                    stage_span.set_attribute('jenkins.duration_ms', stage_duration_ms)
                    stage_span.set_attribute('jenkins.type', 'stage')
                    stage_span.set_attribute('service.name', 'jenkins-observability')

                    for step_data in stage_data.get('steps', []):
                        step_start_time = (
                            datetime.datetime.fromtimestamp(step_data['start_time'] / 1000.0)
                            if step_data['start_time']
                            else stage_start_time
                        )
                        step_duration_ms = step_data.get('duration', 0)
                        step_end_time = step_start_time + datetime.timedelta(milliseconds=step_duration_ms)

                        # Convert to nanoseconds for OpenTelemetry
                        step_start_ns = int(step_start_time.timestamp() * 1_000_000_000)
                        step_end_ns = int(step_end_time.timestamp() * 1_000_000_000)

                        with self.tracer.start_as_current_span(
                            name=f'{step_data["step_name"]}',
                            start_time=step_start_ns,
                        ) as step_span:
                            step_span.set_attribute('jenkins.job', job_name)
                            step_span.set_attribute('jenkins.build_number', build_data['number'])
                            step_span.set_attribute('jenkins.stage_name', stage_data['stage_name'])
                            step_span.set_attribute('jenkins.step_name', step_data['step_name'])
                            step_span.set_attribute('jenkins.step_id', step_data.get('step_id', ''))
                            step_span.set_attribute('jenkins.status', step_data.get('status', 'UNKNOWN'))
                            step_span.set_attribute('jenkins.duration_ms', step_duration_ms)
                            step_span.set_attribute('jenkins.step_type', step_data.get('type', 'STEP'))
                            step_span.set_attribute('jenkins.type', 'step')
                            step_span.set_attribute('service.name', 'jenkins-observability')
                            step_span.end(step_end_ns)

                    stage_span.end(stage_end_ns)

            build_span.end(build_end_ns)

        print(f'published trace for {job_name} build {build_data["number"]} with {len(steps_data)} stages')

        # Force flush to ensure spans are sent
        try:
            print('Attempting to flush spans...')
            result = self.span_processor.force_flush(timeout_millis=5000)
            print(f'Flush result: {result}')
            if not result:
                print('Flush returned False - spans may not have been sent')
        except Exception as e:
            print(f'Error during flush: {e}')
            import traceback
            traceback.print_exc()


async def publish_jenkins_traces(config: dict):
    jenkins_url = config['base_url']
    username = config['username']
    token = config['token']
    pipelines = config['pipelines']

    tempo_endpoint = config.get('tempo_endpoint', 'http://localhost:4318')
    trace_publisher = TracePublisher(tempo_endpoint)

    async with JenkinsClient(jenkins_url, username, token) as jenkins_client:
        build_fetcher = JenkinsBuildFetcher(jenkins_client)

        for pipeline in pipelines:
            print(f'fetching builds for {pipeline}')
            builds = await build_fetcher.get_job_builds(pipeline)
            if not builds:
                print(f'no builds found for {pipeline}')
                continue

            for build in sorted(builds, key=lambda b: b['timestamp']):
                print(f'processing build {build["number"]} for {pipeline}')
                steps_data = await build_fetcher.get_build_steps(pipeline, build['number'])
                trace_publisher.publish_build_trace_with_steps(pipeline, build, steps_data)
                await asyncio.sleep(0.1)


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
        end_time = (
            datetime.datetime.fromtimestamp((timestamp_ms + duration_ms) / 1000)
            if timestamp_ms and duration_ms
            else None
        )

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

    async with JenkinsClient(config['base_url'], config['username'], config['token']) as jenkins_client:
        exporter = JenkinsBuildExporter(jenkins_client, args.workers)

        for pipeline_path in config['pipelines']:
            try:
                await exporter.export_pipeline_builds(pipeline_path, args.output)
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

    async with JenkinsClient(config['base_url'], config['username'], config['token']) as jenkins_client:
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


async def traces_command(args):
    config = load_config(pathlib.Path(args.config))
    await publish_jenkins_traces(config)


async def list_command(args):
    config = load_config(pathlib.Path(args.config))

    async with JenkinsClient(config['base_url'], config['username'], config['token']) as jenkins_client:
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

    trigger_parser = subparsers.add_parser('trigger', help='trigger jenkins jobs')
    trigger_parser.add_argument('--config', required=True, help='path to jenkins configuration file')

    list_parser = subparsers.add_parser('list', help='list jenkins builds')
    list_parser.add_argument('--config', required=True, help='path to jenkins configuration file')
    list_parser.add_argument('--job', help='specific job to list builds for (if not provided, lists all jobs in config)')

    traces_parser = subparsers.add_parser('traces', help='publish jenkins traces to tempo with step-level granularity')
    traces_parser.add_argument('--config', required=True, help='path to jenkins configuration file')

    args = parser.parse_args()

    if args.command == 'export':
        await export_command(args)
    elif args.command == 'trigger':
        await execute_job_schedule(args)
    elif args.command == 'list':
        await list_command(args)
    elif args.command == 'traces':
        await traces_command(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
