#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker images"
    echo "  up          Build and start all services"
    echo "  down        Stop and remove all services"
    echo "  logs        Tail logs from all services"
    echo "  clean       Stop services and remove volumes"
    echo "  backend     Build and run only the backend locally (no Docker)"
    echo "  frontend    Build and run only the frontend locally (no Docker)"
    echo ""
}

build_docker() {
    echo "Building Docker images..."
    docker compose build
    echo "Done."
}

up() {
    echo "Building and starting services..."
    docker compose up --build -d
    echo ""
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8080"
    echo ""
}

down() {
    echo "Stopping services..."
    docker compose down
}

logs() {
    docker compose logs -f
}

clean() {
    echo "Stopping services and removing volumes..."
    docker compose down -v
    echo "Done."
}

build_backend_local() {
    echo "Building backend..."
    cd "$SCRIPT_DIR/backend"
    CGO_ENABLED=1 go build -o bin/notes-api .
    echo "Running backend on :8080"
    mkdir -p dbstore
    ./bin/notes-api
}

build_frontend_local() {
    echo "Installing frontend dependencies..."
    cd "$SCRIPT_DIR/frontend"
    pnpm install
    echo "Starting frontend dev server on :5173"
    pnpm dev
}

case "${1:-}" in
    build)    build_docker ;;
    up)       up ;;
    down)     down ;;
    logs)     logs ;;
    clean)    clean ;;
    backend)  build_backend_local ;;
    frontend) build_frontend_local ;;
    *)        usage ;;
esac
