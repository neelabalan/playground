#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: $0 <max_suffix_number>"
  exit 1
fi

MAX_SUFFIX_NUMBER=$1
BASE_URL="https://huggingface.co/datasets/mteb/raw_arxiv/resolve/main/train_"

for ((i=0; i<=MAX_SUFFIX_NUMBER; i++)); do
  URL="$BASE_URL$i.jsonl.gz"
  FILENAME="filename_$i.jsonl.gz"

  echo "Downloading $URL..."
  curl -L -o "$FILENAME" "$URL"

  if [ $? -eq 0 ]; then
    echo "Downloaded $FILENAME successfully."
    echo "Extracting $FILENAME..."
    gzip -dk "$FILENAME"

    if [ $? -eq 0 ]; then
      echo "Extraction completed for $FILENAME."
    else
      echo "Error extracting $FILENAME."
    fi
  else
    echo "Failed to download $URL."
  fi
done

