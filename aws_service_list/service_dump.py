import glob
import json
import urllib.request
import zipfile
from pathlib import Path

# list of services with AWS CLI
# aws services list


def download_github_repo(repo_url: str, output_dir: str, branch: str = 'main') -> bool:
    parts = repo_url.split('/')
    owner, repo_name = parts[-2], parts[-1]

    zip_url = f'https://codeload.github.com/{owner}/{repo_name}/zip/refs/heads/{branch}'

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir_path / f'{repo_name}.zip'
    urllib.request.urlretrieve(zip_url, str(zip_path))

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)

    zip_path.unlink()
    print(f'Repository {repo_name} downloaded and extracted to {output_dir_path}')
    return Path(output_dir).exists()


def unique_dicts(dicts):
    seen = set()
    return [d for d in dicts if not (t := tuple(sorted(d.items()))) in seen and not seen.add(t)]


def get_service_list(file_list: list[str]) -> list[dict[str, str]]:
    service_list = []
    for file_path in file_list:
        with open(file_path, 'r') as f:
            data = json.load(f)
            service_list.append(
                {
                    'fullname': data.get('metadata', {}).get('serviceFullName', ''),
                    'abbr': data.get('metadata', {}).get('serviceAbbreviation', ''),
                }
            )
    # return list(filter(None, (set(service_list))))
    return unique_dicts(service_list)


def run():
    repo_name = 'botocore'
    branch = 'develop'
    url = f'https://github.com/boto/{repo_name}'
    download_github_repo(url, repo_name, branch)
    file_list = glob.glob('botocore/botocore-develop/botocore/data/**/service-2.json', recursive=True)
    service_list = get_service_list(file_list)
    with open('service_list.json', 'w') as _file:
        json.dump(service_list, _file, indent=4)
    print('Service list dumped to service_list.json')


if __name__ == '__main__':
    run()
