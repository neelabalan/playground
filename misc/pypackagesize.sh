#!/bin/bash

set -e

usage() {
  echo "Usage: $0 <package-name> [--clean] [--package-manager <pip|uv>] [--python <python interpreter to use>]"
  echo "Sample usages:"
  echo "sh pypackagesize.sh ray --clean --package-manager uv --python python3.11"
  echo "sh pypackagesize.sh ray --python \"uvx python3.11\""
  echo "sh pypackagesize.sh $(cat requirements.txt) --python python3.11 --package-manager uv"
  exit 1
}

if [ -z "$1" ]; then
  usage
fi

PACKAGES=()
CLEAN=false
PKG_MANAGER="pip"
PYTHON="python3"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)
      CLEAN=true
      shift
      ;;
    --package-manager)
      PKG_MANAGER="$2"
      shift 2
      ;;
    --python)
      PYTHON="$2"
      shift 2
      ;;
    *)
      PACKAGES+=("$1")
      shift
      ;;
  esac
done

echo $PACKAGE

TMPDIR=$(mktemp -d -t pkgsize-XXXXX)
VENV_DIR="$TMPDIR/.venv"

if [ "$PKG_MANAGER" = "uv" ]; then
  if ! command -v uv > /dev/null; then
    echo "uv is not installed or not in PATH"
    exit 1
  fi
  uv venv --python $PYTHON "$VENV_DIR" > /dev/null
  source "$VENV_DIR/bin/activate"
  uv pip install --no-cache "${PACKAGES[@]}" > /dev/null 2>&1
else
  $PYTHON -m venv "$VENV_DIR" > /dev/null
  source "$VENV_DIR/bin/activate"
  # not necessary
  # $PYTHON -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
  python -m pip install "${PACKAGES[@]}" > /dev/null 2>&1
fi

SITE_DIR=$(python -c "import site; print(site.getsitepackages()[0])")
echo "Getting package size from $SITE_DIR"
SIZE=$(du -sh "$SITE_DIR" | awk '{print $1}')
echo "Total installed size (including dependencies): $SIZE"

deactivate

if [ "$CLEAN" = true ]; then
  rm -rf "$TMPDIR"
else
  echo "Temporary venv kept in: $TMPDIR"
fi