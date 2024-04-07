#!/usr/bin/python3

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import pathlib
import subprocess
import tempfile
import typing

import chromadb
import requests
from chromadb.utils import embedding_functions
from rich import print
from rich.console import Console
from rich.table import Table

token = os.getenv('RAINDROP_TOKEN')
app_dir = pathlib.Path.home() / '.qd'
app_dir.mkdir(exist_ok=True, parents=True)

db_client = chromadb.PersistentClient(path=str(app_dir / 'bookmarks_db'))
collection = db_client.get_or_create_collection('allbookmarks', embedding_function= embedding_functions.SentenceTransformerEmbeddingFunction('all-mpnet-base-v2'))
logging.basicConfig(level=logging.INFO)


def get_raindrops(dump: bool = True) -> list[dict[str, typing.Any]]:
    if not token:
        raise ValueError('Missing RAINDROP_TOKEN environment variable')

    headers = {'Authorization': f'Bearer {token}'}
    data = []
    collection_id = 0
    page = 1

    logging.info('Fetching Raindrop bookmarks')
    while True:
        url = f'https://api.raindrop.io/rest/v1/raindrops/{collection_id}?page={page}'
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            break

        page_data = response.json()
        data.extend(page_data['items'])

        # If there are no more items, break the loop
        if not page_data['items']:
            break

        page += 1
    extracted_data = []
    for item in data:
        extracted_data.append(
            {
                'link': item.get('link'),
                'title': item.get('title'),
                'excerpt': item.get('excerpt'),
                'created': item.get('created'),
            }
        )
    if dump:
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        with open(app_dir / 'raindrop_bookmarks.json', 'w') as f:
            json.dump(extracted_data, f, indent=4)
        with open(app_dir / f'raindropfullbackup_{timestamp}.json', 'w') as f:
            json.dump(data, f, indent=4)
    logging.info('Dumped Raindrop bookmarks to file')
    return extracted_data


def add_to_vectordb(data: list[dict[str, str]]) -> chromadb.Collection:
    documents = [item['title'] + '    ' + item['excerpt'] for item in data]
    metadatas = [{'link': item['link'], 'title': item['title']} for item in data]
    logging.info('Adding Raindrop bookmarks to VectorDB')
    collection.upsert(ids=[item['link'] for item in data], documents=documents, metadatas=metadatas)
    logging.info('Completed adding Raindrop bookmarks to VectorDB')
    return collection


def build_table(data: list[dict[str, str]]) -> Table:
    table = Table.grid(expand=True)
    table.add_column(max_width=2, no_wrap=True)
    table.add_column(max_width=25, no_wrap=True, style='grey74')
    table.add_column(max_width=30, no_wrap=True, style='blue')
    for count, entry in enumerate(data):
        table.add_row(str(count) + ':', entry.get('title'), entry.get('link'))
    return table


def query_bookmark(query: str | None = None, n: int = 50):
    results: list[dict[str, str]] = []
    if query:
        _response = collection.query(query_texts=[query], n_results=n)
        results = [
            {
                'link': metadata['link'],
                'title': metadata['title'],
            }
            for metadata in _response['metadatas'][0]
        ]  # type: ignore
    else:
        with open(app_dir / 'raindrop_bookmarks.json', 'r') as _file:
            results = json.load(_file)

    _tempfile = tempfile.NamedTemporaryFile(mode='w', delete=True)

    console = Console(color_system='256', record=True, file=_tempfile)
    table = build_table(results)

    console.print(table, overflow='ellipsis', soft_wrap=True, end='')

    selected = subprocess.Popen(
        f'cat {_tempfile.name} | fzf --multi --ansi',
        shell=True,
        stdout=subprocess.PIPE,
    ).communicate()[0]
    linenos: list[int] = []
    if selected:
        lines = selected.decode('utf-8').split('\n')
        linenos = [int(line.split(':')[0].strip()) for line in lines if line]
        table = Table(expand=True, show_lines=True)
        table.add_column('title', max_width=5, style='grey74')
        table.add_column('link', max_width=30, style='blue', no_wrap=True)
        for index in linenos:
            table.add_row(results[index].get('title'), results[index].get('link'))
        print('\n\n')
        print(table)
        print('\n\n')
    _tempfile.close()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Query bookmarks.')
    parser.add_argument('--query', type=str, help='The query to search for.')
    parser.add_argument('--n', type=int, help='n_results from similarity search')
    parser.add_argument('--dump', action='store_true', default=False, help='Dump the raindrop bookmarks to a file')

    return parser.parse_args()


def run():
    args = parse_arguments()

    if args.dump:
        _ = add_to_vectordb(get_raindrops())
    query_bookmark(args.query, args.n)


if __name__ == '__main__':
    run()
