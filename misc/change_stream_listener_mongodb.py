import asyncio
import json
import os
import sys
import threading
from typing import Callable
from typing import Dict
from typing import List

import pymongo
from loguru import logger


class SerializableTokenCache:
    def __init__(self, path):
        self.path = path
        self._lock = threading.RLock()
        self._cache = None

    def __str__(self):
        return str(self._cache)

    def load(self):
        try:
            with self._lock:
                with open(self.path, 'r') as token_cache:
                    self._cache = json.load(token_cache)
        except FileNotFoundError as err:
            logger.error('Specified file not found')
        return self._cache

    def dump(self, token: Dict):
        try:
            with self._lock:
                with open(self.path, 'w') as token_cache:
                    json.dumps(token, token_cache)
                    self._cache = token
        except FileNotFoundError as err:
            logger.error('Specified file not found')


class ChangeStreamListener(threading.Thread):
    def __init__(self, db_object: pymongo.database.Database, collection_names: List):
        super(ChangeStreamListener, self).__init__()
        self.db = db_object
        self.collection_names = collection_names
        self.collection = None
        self.token_cache = StopAsyncIteration('token.json')

    def check_conn(self):
        try:
            client = self.db.client
            client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError as err:
            logger.error('pymongo Error ', err)
            sys.exit(0)

        if not self.collection_names or not set(self.collection_names).intersection(
            self.db.list_collection_names()
        ) == set(self.collection_names):
            logger.error(f'Listed collection not found - {self.collection_names}')
            sys.exit(0)

    def init_listener(
        self,
        pipeline: List = [{'$match': {'operationType': 'insert'}}],
        on_change: Callable = None,
    ):
        self.check_conn()
        self.loop = asyncio.new_event_loop()
        pipeline.append({'$match': {'ns.coll': {'$in': self.collection_names}}})

        # each callback to be called exactly once
        self.loop.call_soon_threadsafe(self.listener, *[pipeline, on_change])
        logger.info('Listener initialized...')

    def run(self):
        asyncio.set_event_loop(self.loop)
        logger.info('Starting loop...')
        self.loop.run_forever()

    def listener(self, pipeline: List, on_change: Callable):
        try:
            token = self.token_cache.load()
            if not token:
                # cache the current token
                cursor = self.db.watch(pipeline)
                self.token_cache.dump(cursor.resume_token)

            with self.db.watch(pipeline, resume_after=token if token else None) as stream:
                for change in stream:
                    self.token_cache.dump(stream.resume_token)
                    if callable(on_change):
                        on_change(change)
                    logger.info(f'change -- {change}')
                    logger.info(f'resume token -- {self.token_cache}')
        except KeyboardInterrupt:
            logger.info('Keyboard interrupt')
            self.exit()

    def exit(self):
        self.loop.stop()
        logger.info('Async loop closed')
        try:
            logger.info('exiting...')
            sys.exit(0)
        except SystemExit:
            os._exit(0)
