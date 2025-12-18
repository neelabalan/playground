#!/usr/bin/env bash

set -e

RACKET_VERSION=${RACKET_VERSION:-8.17}
TARGETARCH=${TARGETARCH:-arm64}

if [ -z "${VSCODE_SERVER_VERSION}" ]; then
    CODE_PATH=$(which code 2>/dev/null)
    if [ -n "${CODE_PATH}" ]; then
        echo "Found VS Code at: ${CODE_PATH}"
        VSCODE_SERVER_VERSION=$("${CODE_PATH}" --version 2>/dev/null | sed -n '2p')
        if [ -n "${VSCODE_SERVER_VERSION}" ]; then
            echo "detected VS Code commit from host: ${VSCODE_SERVER_VERSION}"
        else
            echo "warning: Could not detect VS Code commit, using 'latest'"
            VSCODE_SERVER_VERSION="latest"
        fi
    else
        echo "VS Code CLI not found, using 'latest'"
        VSCODE_SERVER_VERSION="latest"
    fi
else
    echo "using specified VS Code commit: ${VSCODE_SERVER_VERSION}"
fi

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
