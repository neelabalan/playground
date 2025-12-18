#!/bin/bash

set -e

EXTENSIONS_FILE=${1:-/tmp/extensions.txt}

if [ ! -f "$EXTENSIONS_FILE" ]; then
    echo "extensions file not found: $EXTENSIONS_FILE"
    exit 0
fi

VSCODE_SERVER_BIN=$(find /root/.vscode-server/bin -mindepth 1 -maxdepth 1 -type d | head -n 1)

if [ -z "$VSCODE_SERVER_BIN" ]; then
    echo "VS Code Server bin directory not found"
    exit 1
fi

echo "installing extensions from: $EXTENSIONS_FILE"
echo "using VS Code Server at: $VSCODE_SERVER_BIN"

while IFS= read -r extension || [ -n "$extension" ]; do
    # skip empty lines and comments
    [[ -z "$extension" || "$extension" =~ ^# ]] && continue
    
    echo "installing extension: $extension"
    "$VSCODE_SERVER_BIN/bin/code-server" --install-extension "$extension" || echo "failed to install $extension"
done < "$EXTENSIONS_FILE"

echo "extension installation complete"
