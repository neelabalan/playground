import argparse
import functools
import pathlib
import random
import shutil
import sqlite3
import time

import matplotlib.pyplot as plt

lines = []
sqlite_db_file = pathlib.Path('text.db')
file_system_directory = pathlib.Path('text_directory')


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f'{func.__name__} took {elapsed_time} seconds')
        return elapsed_time

    return wrapper


# def random_string(length):
#     return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_text():
    return '\n'.join(random.sample(lines, random.randint(1, len(lines))))


@timeit
def write_file_system(iterations):
    file_system_directory.mkdir(exist_ok=True)

    for i in range(iterations):
        filename = file_system_directory / f'text_{i}.txt'
        content = get_text()
        with filename.open('w') as file:
            file.write(content)


@timeit
def read_file_system(iterations):
    contents = []
    for i in range(iterations):
        filename = file_system_directory / f'text_{i}.txt'
        with filename.open('r') as file:
            contents.append(file.read())


@timeit
def write_sqlite(iterations):
    with sqlite3.connect(sqlite_db_file) as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS text (id INTEGER PRIMARY KEY, content TEXT)""")

        contents = [get_text() for _ in range(iterations)]
        # c.executemany('''INSERT INTO text (content) VALUES (?)''', contents)
        for content in contents:
            c.execute("""INSERT INTO text (content) VALUES (?)""", (content,))


@timeit
def read_sqlite():
    with sqlite3.connect(sqlite_db_file) as conn:
        c = conn.cursor()
        c.execute("""SELECT * FROM text""")
        rows = c.fetchall()


def run_benchmark(iterations, repeats):
    # Initialize lists to store the times
    file_system_write_times = []
    file_system_read_times = []
    sqlite_write_times = []
    sqlite_read_times = []

    for itr in range(repeats):
        # Run the tests
        print(f'running iteration {itr + 1} of {repeats}')
        file_system_write_times.append(write_file_system(iterations))
        file_system_read_times.append(read_file_system(iterations))
        sqlite_write_times.append(write_sqlite(iterations))
        sqlite_read_times.append(read_sqlite())
        cleanup([sqlite_db_file, file_system_directory])

    # Plot the results
    x = range(1, repeats + 1)
    plt.clf()
    plt.plot(x, file_system_write_times, marker='o', label='File System Write')
    plt.plot(x, file_system_read_times, marker='o', label='File System Read')
    plt.plot(x, sqlite_write_times, marker='o', label='SQLite Write')
    plt.plot(x, sqlite_read_times, marker='o', label='SQLite Read')

    plt.xlabel('Cycles')
    plt.ylabel('Time (s)')
    plt.title(f'Benchmark Results {iterations} iterations')
    plt.legend()
    plt.savefig(f'images/benchmark_results_{iterations}.png')


def cleanup(filepaths):
    print('Cleaning up files')
    for filepath in filepaths:
        if filepath.is_dir():
            shutil.rmtree(filepath)
        else:
            filepath.unlink()
        print(f'Removed directory {filepath}')


def collect_data(args):
    run_benchmark(100, 5)
    run_benchmark(1000, 5)
    run_benchmark(10000, 5)


def run_bench(args):
    write_file_system(args.iterations)
    read_file_system(args.iterations)

    write_sqlite(args.iterations)
    read_sqlite()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark file system and SQLite.')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations')
    parser.add_argument('--filename', type=str, help='Maximum size of random strings')
    args = parser.parse_args()
    with open(args.filename, 'r') as file:
        lines = file.readlines()

    # run_bench(args)
    collect_data(args)
