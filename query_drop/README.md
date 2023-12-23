# QueryDrop (qd)

QueryDrop is a Python script that interacts with the Raindrop.io API to fetch and process bookmark data.

## Description

The script uses the Raindrop.io API to fetch all bookmarks (referred to as "raindrops") from a user's account. It then extracts the link and title from each bookmark and stores them in a local database using the `chromadb` (Vector database) package.
In the context of QueryDrop, you can use `fzf`` to interactively search and select a bookmark from the command line using only fzf or similarity search. Once a bookmark is selected, you can use the corresponding link for further processing.

## Installation

To install the necessary dependencies, navigate to the project directory and run the following command:

```bash
pip install -r requirements.txt
```

## Usage

Before running the script, you need to set the RAINDROP_TOKEN environment variable to your Raindrop.io API token. You can do this in a Unix-based system with the following command:

```bash
export RAINDROP_TOKEN=your_token_here
```

By default, the script will fetch all bookmarks from your Raindrop.io account and store them in a local database. The database is stored in the .qd directory in your home directory.