import argparse
import json
import logging
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Extract packets from JSON export.')
    parser.add_argument('input_json', help='Path to the input JSON file')
    parser.add_argument('output_folder', help='Path to the output folder')
    parser.add_argument('--filter', help='Filter packets by a specific field (e.g., IP address)', default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    input_path = Path(args.input_json)
    if not input_path.is_file():
        logging.error(f'Input file {args.input_json} does not exist.')
        sys.exit(1)

    output_path = Path(args.output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        with input_path.open('r') as _file:
            data = json.load(_file)
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON: {e}')
        sys.exit(1)
    except Exception as e:
        logging.error(f'An error occurred while reading the input file: {e}')
        sys.exit(1)

    for idx, packet in enumerate(data, 1):
        try:
            frame_number = packet['_source']['layers']['frame']['frame.number']
            filename = output_path / f'packet-{frame_number}.json'

            if args.filter:
                if args.filter not in json.dumps(packet):
                    continue

            with filename.open('w') as file_:
                json.dump(packet, file_, indent=4)

            logging.info(f'Processed packet {idx}/{len(data)}: frame {frame_number}')

        except KeyError as e:
            logging.warning(f'Missing key {e} in packet {idx}, skipping...')
            continue
        except Exception as e:
            logging.error(f'An error occurred while processing packet {idx}: {e}')
            continue

    logging.info('Packet extraction completed successfully.')


if __name__ == '__main__':
    main()
