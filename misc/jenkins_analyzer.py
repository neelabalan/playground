import argparse
import csv
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import requests


class JenkinsAnalyzer:
    def __init__(self, url: str, job_name: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.job_name = job_name
        self.auth = (username, password)
        self.base_api = f'{self.url}/job/{self.job_name}'

    def get_build_data(self) -> list[dict]:
        builds_url = f'{self.base_api}/api/json?tree=builds[number]'
        response = requests.get(builds_url, auth=self.auth)
        response.raise_for_status()
        builds = response.json().get('builds', [])
        build_data = []
        for build in builds:
            build_number = build['number']
            build_info = self._get_build_info(build_number)
            if build_info:
                timestamp = build_info['timestamp'] / 1000
                duration = build_info['duration'] / 1000
                result = build_info['result']
                triggered_by = self._get_triggered_by(build_info)
                build_data.append(
                    {
                        'build_number': build_number,
                        'start_time': datetime.fromtimestamp(timestamp, tz=timezone.utc),
                        'duration': duration,
                        'result': result,
                        'triggered_by': triggered_by,
                    }
                )
        return build_data

    def _get_build_info(self, build_number: int) -> dict:
        build_url = f'{self.base_api}/{build_number}/api/json'
        response = requests.get(build_url, auth=self.auth)
        if response.status_code != 200:
            return {}
        return response.json()

    def _get_triggered_by(self, build_info: dict) -> str:
        for action in build_info.get('actions', []):
            if action.get('_class') == 'hudson.model.CauseAction':
                for cause in action.get('causes', []):
                    if cause.get('_class') == 'hudson.model.Cause$UserIdCause':
                        return cause.get('userId', 'Unknown')
                    elif 'shortDescription' in cause:
                        return cause['shortDescription']
        return 'Unknown'

    def get_stage_data_for_build(self, build_number: int) -> list[dict]:
        wfapi_url = f'{self.base_api}/{build_number}/wfapi/describe'
        response = requests.get(wfapi_url, auth=self.auth)
        if response.status_code != 200:
            return []
        wfapi_data = response.json()
        stages = wfapi_data.get('stages', [])
        stage_data = []
        for stage in stages:
            stage_name = stage['name']
            stage_duration = stage['durationMillis'] / 1000
            stage_data.append({'build_number': build_number, 'stage_name': stage_name, 'duration': stage_duration})
        return stage_data

    def get_stage_data(self) -> list[dict]:
        build_data = self.get_build_data()
        stage_data = []
        for build in build_data:
            build_number = build['build_number']
            stages = self.get_stage_data_for_build(build_number)
            stage_data.extend(stages)
        return stage_data

    def calculate_average_successful_duration(self) -> float:
        build_data = self.get_build_data()
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        successful_builds = [
            build for build in build_data if build['result'] == 'SUCCESS' and build['start_time'] >= thirty_days_ago
        ]
        if not successful_builds:
            return 0.0
        total_duration = sum(build['duration'] for build in successful_builds)
        return total_duration / len(successful_builds)

    def detect_outliers(self) -> list[int]:
        build_data = self.get_build_data()
        durations = [build['duration'] for build in build_data]
        if len(durations) < 4:
            return []
        durations.sort()
        n = len(durations)
        q1 = durations[int(n * 0.25)]
        q3 = durations[int(n * 0.75)]
        iqr = q3 - q1
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr
        outliers = [
            build['build_number']
            for build in build_data
            if build['duration'] < lower_bound or build['duration'] > upper_bound
        ]
        return outliers

    def export_to_csv(self, builds_file: str = 'builds.csv', stages_file: str = 'stages.csv'):
        build_data = self.get_build_data()
        stage_data = self.get_stage_data()
        with open(builds_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['build_number', 'start_time', 'duration', 'result', 'triggered_by'])
            writer.writeheader()
            for build in build_data:
                writer.writerow(
                    {
                        'build_number': build['build_number'],
                        'start_time': build['start_time'].isoformat(),
                        'duration': build['duration'],
                        'result': build['result'],
                        'triggered_by': build['triggered_by'],
                    }
                )
        with open(stages_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['build_number', 'stage_name', 'duration'])
            writer.writeheader()
            for stage in stage_data:
                writer.writerow(stage)


def main():
    parser = argparse.ArgumentParser(description='Jenkins Job Analyzer')
    parser.add_argument('--url', required=True, help='Jenkins URL')
    parser.add_argument('--job', required=True, help='Jenkins job name')
    parser.add_argument('--username', required=True, help='Jenkins username')
    parser.add_argument('--password', required=True, help='Jenkins password or API token')
    parser.add_argument('--export', action='store_true', help='Export data to CSV')
    args = parser.parse_args()

    analyzer = JenkinsAnalyzer(args.url, args.job, args.username, args.password)
    build_data = analyzer.get_build_data()
    if build_data:
        last_build = build_data[0]
        print(f'Last build ({last_build["build_number"]}):')
        print(f'  Start time: {last_build["start_time"]}')
        print(f'  Duration: {last_build["duration"]:.2f} seconds')
        print(f'  Triggered by: {last_build["triggered_by"]}')
        stages = analyzer.get_stage_data_for_build(last_build['build_number'])
        for stage in stages:
            print(f'  Stage {stage["stage_name"]}: {stage["duration"]:.2f} seconds')

    avg_duration = analyzer.calculate_average_successful_duration()
    print(f'Average successful duration in the past 30 days: {avg_duration:.2f} seconds')

    outliers = analyzer.detect_outliers()
    print('Outlier build numbers:', outliers)

    if args.export:
        analyzer.export_to_csv()
        print('Data exported to builds.csv and stages.csv')


if __name__ == '__main__':
    main()
