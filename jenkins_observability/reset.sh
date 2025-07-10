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

docker stop $(docker ps -q) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker rmi $(docker images -q) 2>/dev/null || true
docker image prune -af >/dev/null 2>&1
docker volume rm $(docker volume ls -q) 2>/dev/null || true
docker volume prune -f >/dev/null 2>&1
docker network prune -f >/dev/null 2>&1
docker builder prune -af >/dev/null 2>&1

if [ -d "container" ]; then
    sudo rm -rf container
fi

docker system prune -af --volumes >/dev/null 2>&1

if command_exists systemctl; then
    sudo systemctl restart docker >/dev/null 2>&1 || true
fi

echo "Reset complete"
echo "Verification:"
docker images
docker container ls -a
docker volume ls
