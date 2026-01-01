import argparse
import datetime
import json
import pathlib
import pickle
import sys
import typing as t


def get_vivaldi_session_dir() -> pathlib.Path:
    home = pathlib.Path.home()
    if sys.platform == 'darwin':
        vivaldi_dir = home / 'Library' / 'Application Support' / 'Vivaldi' / 'Default'
    elif sys.platform == 'linux':
        vivaldi_dir = home / '.config' / 'vivaldi' / 'Default'
    else:
        raise NotImplementedError(f'unsupported platform: {sys.platform}')
    return vivaldi_dir


def extract_urls_from_entries(entries: list) -> list[str]:
    urls: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if 'url' in entry:
            urls.append(entry['url'])
        for value in entry.values():
            if isinstance(value, list):
                urls.extend(extract_urls_from_entries(value))
            elif isinstance(value, dict):
                urls.extend(extract_urls_from_entries([value]))
    return urls


def extract_urls_from_text(content: str) -> list[str]:
    urls: list[str] = []
    parts = content.split('http')
    for part in parts[1:]:
        terminators = ['\x00', '\n', '\r', ' ', '"', "'"]
        positions = [part.find(c) for c in terminators]
        valid_positions = [pos for pos in positions if pos != -1]
        url_end = min(valid_positions) if valid_positions else len(part)
        url = 'http' + part[:url_end]
        if '://' in url and len(url) > 10:
            urls.append(url)
    return list(set(urls))


def read_binary_session_file(file_path: pathlib.Path) -> dict[str, t.Any]:
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
            urls = extract_urls_from_entries([data])
            return {'urls': urls, 'raw_data': str(data)[:500]}
    except Exception:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                urls = extract_urls_from_text(content)
                return {'urls': urls}
        except Exception as e:
            return {'error': str(e)}


def create_session_info(child: dict[str, t.Any], sessions_dir: pathlib.Path) -> dict[str, t.Any]:
    session_info: dict[str, t.Any] = {
        'title': child.get('title', 'Untitled'),
        'created': datetime.datetime.fromtimestamp(child.get('createtime', 0) / 1000).isoformat(),
        'modified': datetime.datetime.fromtimestamp(child.get('modifytime', 0) / 1000).isoformat(),
        'tabs_count': child.get('tabscount', 0),
        'windows_count': child.get('windowscount', 0),
        'urls': [],
    }
    filename = child.get('filename')
    if not filename:
        return session_info
    bin_file = sessions_dir / filename
    if not bin_file.exists():
        return session_info
    bin_data = read_binary_session_file(bin_file)
    session_info['urls'] = bin_data.get('urls', [])
    return session_info


def parse_session_metadata(sessions_data: list, sessions_dir: pathlib.Path) -> list[dict[str, t.Any]]:
    parsed_sessions: list[dict[str, t.Any]] = []
    for item in sessions_data:
        if not isinstance(item, dict) or 'children' not in item:
            continue
        for child in item['children']:
            if not isinstance(child, dict) or child.get('type') != 0:
                continue
            session_info = create_session_info(child, sessions_dir)
            parsed_sessions.append(session_info)
    return parsed_sessions


def process_sessions(vivaldi_dir: pathlib.Path) -> list[dict[str, t.Any]]:
    sessions_dir = vivaldi_dir / 'Sessions'
    sessions_json = sessions_dir / 'sessions.json'

    all_sessions: list[dict[str, t.Any]] = []

    if not sessions_json.exists():
        return all_sessions

    try:
        with open(sessions_json, 'r', encoding='utf-8') as f:
            sessions_data = json.load(f)
            parsed = parse_session_metadata(sessions_data, sessions_dir)
            all_sessions.extend(parsed)
    except Exception as e:
        print(f'error reading sessions.json: {e}')

    return all_sessions


def export_sessions(sessions: list[dict[str, t.Any]], output_file: str) -> None:
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description='Export Vivaldi save sessions as JSON')
    parser.add_argument('--output', type=str, default='vivaldi_sessions.json', help='Output JSON file')
    parser.add_argument('--vivaldi-dir', type=str, help='Custom Vivaldi directory path')

    args = parser.parse_args()

    vivaldi_dir = pathlib.Path(args.vivaldi_dir) if args.vivaldi_dir else get_vivaldi_session_dir()

    if not vivaldi_dir.exists():
        print(f'error: vivaldi directory not found at {vivaldi_dir}')
        return

    sessions = process_sessions(vivaldi_dir)

    if not sessions:
        print('no sessions found')
        return

    export_sessions(sessions, args.output)
    print(f'exported {len(sessions)} session(s) to {args.output}')


if __name__ == '__main__':
    main()
