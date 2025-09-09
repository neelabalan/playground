import httpx

JENKINS_URL: str = 'http://localhost:8080'
JOB_NAME: str = 'ecgo-docker-pipeline'
USERNAME: str = 'jenkins'
PASSWORD: str = 'admin'

base_api: str = f'{JENKINS_URL.rstrip("/")}/job/{JOB_NAME}'
builds_url: str = f'{base_api}/api/json?tree=builds[number]'

with httpx.Client() as client:
    response = client.get(builds_url, auth=(USERNAME, PASSWORD))
    response.raise_for_status()
    builds = response.json().get('builds', [])

print(f"Builds for job '{JOB_NAME}':")
for build in builds:
    print(f'Build number: {build["number"]}')
