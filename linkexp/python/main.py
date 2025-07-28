import argparse
import asyncio

from test_req import run_seq
from test_req_async import run_async


def run(args: argparse.Namespace):
    if not args.concurrent:
        run_seq()
    else:
        asyncio.run(run_async(args.max_req))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark the usage of lru_cache in Python.')
    parser.add_argument(
        '--concurrent',
        type=bool,
        default=False,
        help='To run the link checker concurrently or not',
    )
    parser.add_argument(
        '--max_req',
        type=int,
        default=10,
        help='Semaphore val',
    )
    args = parser.parse_args()
    run(args)
