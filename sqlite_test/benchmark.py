import argparse
import functools
import pathlib
import random
import shutil
import sqlite3
import time

lines = []


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f'{func.__name__} took {end_time - start_time} seconds')
        return result

    return wrapper


# def random_string(length):
#     return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def get_text():
    return '\n'.join(random.sample(lines, random.randint(1, len(lines))))


@timeit
def write_file_system(directory, iterations):
    directory = pathlib.Path(directory)
    directory.mkdir(exist_ok=True)

    for i in range(iterations):
        filename = directory / f'text_{i}.txt'
        content = get_text()
        with filename.open('w') as file:
            file.write(content)


@timeit
def read_file_system(directory, iterations):
    directory = pathlib.Path(directory)

    for i in range(iterations):
        filename = directory / f'text_{i}.txt'
        with filename.open('r') as file:
            content = file.read()


@timeit
def write_sqlite(db_file, iterations):
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS text (id INTEGER PRIMARY KEY, content TEXT)""")

        contents = [get_text() for _ in range(iterations)]
        # c.executemany('''INSERT INTO text (content) VALUES (?)''', contents)
        for content in contents:
            c.execute("""INSERT INTO text (content) VALUES (?)""", (content,))


@timeit
def read_sqlite(db_file):
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()
        c.execute("""SELECT * FROM text""")
        rows = c.fetchall()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Benchmark file system and SQLite.')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations')
    parser.add_argument('--filename', type=str, help='Maximum size of random strings')
    args = parser.parse_args()
    with open(args.filename, 'r') as file:
        lines = file.readlines()

    file_system_directory = pathlib.Path('text_directory')
    write_file_system(file_system_directory, args.iterations)
    read_file_system(file_system_directory, args.iterations)

    sqlite_db_file = pathlib.Path('text.db')
    write_sqlite(sqlite_db_file, args.iterations)
    read_sqlite(sqlite_db_file)

    print('Cleaning up files')
    shutil.rmtree(file_system_directory)
    sqlite_db_file.unlink()
