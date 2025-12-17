#!/usr/bin/env bash

set -e

RACKET_VERSION=${RACKET_VERSION:-8.17}
VSCODE_SERVER_VERSION=${VSCODE_SERVER_VERSION:-latest}
TARGETARCH=${TARGETARCH:-arm64}

docker build \
    --build-arg RACKET_VERSION=${RACKET_VERSION} \
    --build-arg TARGETARCH=${TARGETARCH} \
    -f Dockerfile.racket.aarch64 \
    -t racket:${RACKET_VERSION} \
    .

docker build \
    --build-arg RACKET_VERSION=${RACKET_VERSION} \
    --build-arg VSCODE_SERVER_VERSION=${VSCODE_SERVER_VERSION} \
    -f Dockerfile.racket-jupyter \
    -t racket-jupyter:${RACKET_VERSION} \
    .
