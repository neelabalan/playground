#!/bin/bash

set -e

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

if ! command_exists docker; then
    echo "Error: Docker not found"
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo "Error: Docker Compose not found"
    exit 1
fi

if [ -f "docker-compose.yaml" ]; then
    docker-compose down --remove-orphans 2>/dev/null || docker compose down --remove-orphans 2>/dev/null || true
fi

docker rmi customjenkins:latest 2>/dev/null || true

docker volume rm jenkins-data 2>/dev/null || true
docker volume rm jenkins-docker-certs 2>/dev/null || true
docker volume rm postgres_data 2>/dev/null || true

if [ -d "container" ]; then
    sudo rm -rf container
fi

docker network prune -f >/dev/null 2>&1

echo "Reset complete for Jenkins Observability project"
echo "Verification:"
docker images | grep -E "(customjenkins|grafana|postgres)" || echo "No project images found"
docker container ls -a | grep -E "(jenkins-blueocean|grafana|postgres)" || echo "No project containers found"
docker volume ls | grep -E "(jenkins-data|jenkins-docker-certs|postgres_data)" || echo "No project volumes found"
