#!/usr/bin/env python3
import argparse
import gzip
import logging
import pathlib
import time
import traceback

import bson
import bson.json_util
import pymongo
from pymongo.collection import Collection


class GzippedJsonRotatingFileHandler:
    def __init__(self, base_filename, max_mb):
        self.base_filename = base_filename
        self.max_bytes = max_mb * 1024 * 1024
        self.file_counter = 0
        self.current_file = None
        self.current_size = 0
        self.open_new_file()

    def open_new_file(self):
        if self.current_file:
            self.current_file.close()
        filename = f"data/{self.base_filename}.{self.file_counter}.jsonl.gz"
        self.current_filename = pathlib.Path(filename)
        self.current_file = gzip.open(self.current_filename, mode='w')
        self.current_size = 0
        self.file_counter += 1

    def write(self, data: dict):
        current_size = self.current_filename.stat().st_size
        if current_size >= self.max_bytes:
            self.open_new_file()
        self.current_file.write((bson.json_util.dumps(data)+ '\n').encode())

    def close(self):
        if self.current_file:
            self.current_file.close()
            self.current_file = None

def change_stream_listener(collection: Collection, logger: logging.Logger, gzipped_logger: GzippedJsonRotatingFileHandler) -> None:
    try:
        logger.info("Listening to change stream...")
        with collection.watch() as stream:
            for change in stream:
                event_type = change.get("operationType")
                logger.info(f"Change detected: {event_type} at {time.time()}")
                logger.debug(change)
                gzipped_logger.write(change)
    except Exception as e:
        gzipped_logger.close()
        logger.error(f"Error in change stream: {e}")
        traceback.print_exc()
    except KeyboardInterrupt as _:
        gzipped_logger.close()
        logger.error("Intercepted keyboard interrupt")

def main():
    parser = argparse.ArgumentParser(description="MongoDB Change Stream Listener")
    parser.add_argument('--mongo-uri', type=str, default='mongodb://localhost:27017/', help='MongoDB URI')
    parser.add_argument('--database', type=str, default='test_db', help='Database name')
    parser.add_argument('--collection', type=str, default='test_collection', help='Collection name')
    parser.add_argument('--collect-size', type=int, default=10, help='Size in MB before rotating log files')
    parser.add_argument('--output-file', type=str, default='change_stream', help='Base name for output files')
    args = parser.parse_args()

    # Set up logging
    logger = logging.getLogger('ChangeStreamListener')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('logs/change_stream_listener.log')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    gzipped_logger = GzippedJsonRotatingFileHandler(args.output_file, args.collect_size)

    client = pymongo.MongoClient(args.mongo_uri)
    db = client[args.database]
    collection = db[args.collection]

    change_stream_listener(collection, logger, gzipped_logger)

    gzipped_logger.close()

if __name__ == "__main__":
    main()
