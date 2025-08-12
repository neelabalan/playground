import requests

JENKINS_URL = "http://localhost:8080"
JOB_NAME = "ecgo-docker-pipeline"
USERNAME = "jenkins"
PASSWORD = "admin"

base_api = f"{JENKINS_URL.rstrip('/')}/job/{JOB_NAME}"
builds_url = f"{base_api}/api/json?tree=builds[number]"

response = requests.get(builds_url, auth=(USERNAME, PASSWORD))
response.raise_for_status()
builds = response.json().get('builds', [])

print(f"Builds for job '{JOB_NAME}':")
for build in builds:
    print(f"Build number: {build['number']}")
