#!/usr/bin/env python3
import argparse
import gzip
import json
import logging
import time

from pymongo import MongoClient


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
        filename = f"{self.base_filename}.{self.file_counter}.json.gz"
        self.current_file = gzip.open(filename, 'wt')
        self.current_size = 0
        self.file_counter += 1

    def write(self, data):
        json_str = json.dumps(data)
        self.current_file.write(json_str + '\n')
        self.current_size += len(json_str) + 1  # Plus newline
        if self.current_size >= self.max_bytes:
            self.open_new_file()

    def close(self):
        if self.current_file:
            self.current_file.close()
            self.current_file = None

def change_stream_listener(collection, logger, gzipped_logger) -> None:
    try:
        logger.info("Listening to change stream...")
        with collection.watch() as stream:
            for change in stream:
                event_type = change.get("operationType")
                logger.info(f"Change detected: {event_type} at {time.time()}")
                gzipped_logger.write(change)
    except Exception as e:
        logger.error(f"Error in change stream: {e}")

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
    fh = logging.FileHandler('change_stream_listener.log')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Set up GzippedJsonRotatingFileHandler
    gzipped_logger = GzippedJsonRotatingFileHandler(args.output_file, args.collect_size)

    # Set up MongoDB client
    client = MongoClient(args.mongo_uri)
    db = client[args.database]
    collection = db[args.collection]

    # Start the change stream listener
    change_stream_listener(collection, logger, gzipped_logger)

    # Close the gzipped logger
    gzipped_logger.close()

if __name__ == "__main__":
    main()
