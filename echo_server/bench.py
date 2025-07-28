import asyncio
import time
import random
import statistics
import argparse

async def echo_client(host: str, port: int, message: str, results: list[float], semaphore: asyncio.Semaphore) -> None:
    start_time = time.perf_counter()
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.write((message + "\r\n").encode())
        await writer.drain()
        await reader.readline()
        end_time = time.perf_counter()
        results.append(end_time - start_time)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
        semaphore.release()

async def benchmark(host: str, port: int, num_connections: int, messages: list[str], duration: float) -> dict:
    results = []
    semaphore = asyncio.Semaphore(num_connections)
    start_time = time.perf_counter()
    client_tasks = set()

    async def worker() -> None:
        while time.perf_counter() - start_time < duration:
            message = random.choice(messages)
            await semaphore.acquire()
            task = asyncio.create_task(echo_client(host, port, message, results, semaphore))
            client_tasks.add(task)
            task.add_done_callback(client_tasks.discard)

    workers = [asyncio.create_task(worker()) for _ in range(num_connections)]
    try:
        await asyncio.gather(*workers)
    except asyncio.CancelledError:
        print("Benchmark cancelled by user")
    finally:
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        if client_tasks:
            await asyncio.gather(*client_tasks)

    if not results:
        return {"error": "No successful requests"}

    return {
        "total_requests": len(results),
        "mean_time": statistics.mean(results),
        "median_time": statistics.median(results),
        "p95_time": statistics.quantiles(results, n=100)[94],
        "p99_time": statistics.quantiles(results, n=100)[98],
        "min_time": min(results),
        "max_time": max(results),
        "requests_per_second": len(results) / duration,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark an echo server.")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, required=True, help="Server port")
    parser.add_argument("--connections", type=int, default=100, help="Number of concurrent connections")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration of the benchmark in seconds")
    parser.add_argument("--messages", type=str, nargs="+", default=[
        "Hello, World!",
        "This is a test message.",
        "Benchmarking echo server.",
        "Asyncio is powerful.",
        "Python 3.11 is fast."
    ], help="List of messages to send")

    args = parser.parse_args()

    try:
        stats = asyncio.run(benchmark(args.host, args.port, args.connections, args.messages, args.duration))
        print("\nBenchmark Results:")
        for key, value in stats.items():
            print(f"{key}: {value}")
    except KeyboardInterrupt:
        print("\nBenchmark stopped by user")

if __name__ == "__main__":
    main()

