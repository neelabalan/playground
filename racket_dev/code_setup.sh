#!/usr/bin/env bash

set -e

VSCODE_SERVER_VERSION=${1:-latest}

# Get the architecture in the format VS Code expects
# VS Code uses: arm64 for aarch64, x64 for x86_64
ARCH=$(uname -m)
case "${ARCH}" in
    aarch64)
        VSCODE_ARCH="arm64"
        ;;
    x86_64)
        VSCODE_ARCH="x64"
        ;;
    *)
        echo "unsupported architecture: ${ARCH}"
        exit 1
        ;;
esac

if [ "${VSCODE_SERVER_VERSION}" = "latest" ]; then
    COMMIT_ID=$(curl -s "https://update.code.visualstudio.com/api/commits/stable/server-linux-${VSCODE_ARCH}" | grep -o '"[a-f0-9]\{40\}"' | head -n 1 | tr -d '"')
    
    if [ -z "${COMMIT_ID}" ]; then
        echo "failed to fetch commit ID from VS Code API"
        exit 1
    fi
    
    echo "fetched commit ID: ${COMMIT_ID} for architecture: ${VSCODE_ARCH}"
else
    COMMIT_ID="${VSCODE_SERVER_VERSION}"
fi

mkdir -p /root/.vscode-server/bin/${COMMIT_ID}

echo "downloading VS Code Server for linux-${VSCODE_ARCH}..."
if ! curl -L "https://update.code.visualstudio.com/commit:${COMMIT_ID}/server-linux-${VSCODE_ARCH}/stable" -o vscode-server.tar.gz; then
    echo "Failed to download VS Code Server"
    exit 1
fi

echo "extracting VS Code Server..."
tar xzf vscode-server.tar.gz -C /root/.vscode-server/bin/${COMMIT_ID} --strip-components=1
rm vscode-server.tar.gz

# Mark as successfully installed
touch /root/.vscode-server/bin/${COMMIT_ID}/0

echo "VS Code Server installed successfully at: /root/.vscode-server/bin/${COMMIT_ID}"
