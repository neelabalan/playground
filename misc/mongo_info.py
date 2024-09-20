import argparse
import sys
import typing

import pymongo
import pymongo.errors
import rich
import rich.console
import rich.table


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='MongoDB Collection Size Reporter')
    parser.add_argument('--uri', help='MongoDB URI')
    parser.add_argument(
        '--unit', choices=['KB', 'MB', 'GB'], default='MB', help='Unit for displaying sizes (default: MB)'
    )
    return parser.parse_args()


def format_size(size: int, unit: str) -> float:
    if unit == 'KB':
        return size / 1024
    elif unit == 'GB':
        return size / (1024 * 1024 * 1024)
    else:  # Default to MB
        return size / (1024 * 1024)


def get_collection_stats(client: pymongo.MongoClient, unit: str) -> list[dict[str, typing.Any]]:
    results = []
    try:
        for db_name in client.list_database_names():
            db = client[db_name]
            for collection_name in db.list_collection_names():
                stats = db.command('collStats', collection_name)
                results.append(
                    {
                        'db_name': db_name,
                        'collection_name': collection_name,
                        'size': format_size(stats['size'], unit),
                        'storage_size': format_size(stats['storageSize'], unit),
                        'count': stats['count'],
                    }
                )
    except pymongo.errors.PyMongoError as e:
        print(f'Error listing databases: {e}', file=sys.stderr)
    return results


def create_table(results: list[dict[str, typing.Any]], unit: str) -> rich.table.Table:
    table = rich.table.Table(title='MongoDB Collections Size and Document Count')
    table.add_column('Database', justify='left', style='cyan', no_wrap=True)
    table.add_column('Collection', justify='left', style='magenta', no_wrap=True)
    table.add_column(f'Size ({unit})', justify='right', style='green')
    table.add_column(f'Storage Size ({unit})', justify='right', style='green')
    table.add_column('Documents', justify='right', style='green')

    for result in results:
        table.add_row(
            result['db_name'],
            result['collection_name'],
            f'{result["size"]:.2f}',
            f'{result["storage_size"]:.2f}',
            str(result['count']),
        )

    return table


def main() -> None:
    args = parse_arguments()
    console = rich.console.Console()

    try:
        client = pymongo.MongoClient(args.uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # This will raise an exception if connection fails
    except pymongo.errors.PyMongoError as e:
        console.print(f'[bold red]Error connecting to MongoDB:[/bold red] {e}')
        sys.exit(1)

    try:
        results = get_collection_stats(client, args.unit)
        if not results:
            console.print('[yellow]No collections found or unable to retrieve stats.[/yellow]')
            return

        results.sort(key=lambda x: x['size'], reverse=True)
        table = create_table(results, args.unit)
        console.print(table)
    except Exception as e:
        console.print(f'[bold red]An unexpected error occurred:[/bold red] {e}')
        console.print_exception(show_locals=True)
    finally:
        client.close()


if __name__ == '__main__':
    main()
