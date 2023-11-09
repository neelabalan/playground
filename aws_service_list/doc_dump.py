import json
import pathlib
import re
from typing import Dict, List
from urllib.request import urlopen
from xml.etree import ElementTree

import requests
from markdownify import markdownify as md
from bs4 import BeautifulSoup


base_url = "https://docs.aws.amazon.com"


def get_href_links(url: str) -> List[str]:
    response = urlopen(url)
    xml_data = response.read().decode()
    root = ElementTree.fromstring(xml_data)
    return [
        element.attrib["href"] for element in root.iter() if "href" in element.attrib
    ]


# Similar to https://github.com/richarvey/getAWSdocs/blob/master/getAWSdocs.py
def get_valid_xml_links(links: List[str]) -> List[str]:
    pattern = re.compile(r"/([^/]*)/")
    link_list = []
    for link in links:
        # print(f"{href=}")
        if "?" not in link or link.startswith("https://"):
            continue
        url = base_url + link.split("?")[0] + "en_us/" + "landing-page.xml"
        print(f"{url=}")

        response = requests.get(url)
        if (
            response.status_code == 200
            and "userguide" in response.text.lower()
            or "developer guide" in response.text.lower()
        ):
            # print(href)
            matches = pattern.match(link)
            word = matches.group(1) if matches else None
            if word:
                print(word)
            link_list.append(url)
    with open("landing_page_links.json", "w") as _file:
        json.dump(link_list, _file, indent=4)
    return link_list


def get_developer_and_user_guide_links(links: List[str]) -> List[str]:
    filtered_links = []
    for link in links:
        doc_links = get_href_links(link)
        print(f"XML extracted for {link=}")
        filtered_links.extend(
            list(
                filter(
                    lambda x: (
                        x.lower().endswith("/dg/")
                        or x.lower().endswith("/userguide/")
                        or x.lower().endswith("/developerguide/")
                    )
                    and not x.startswith("https://"),
                    doc_links,
                )
            )
        )
    filtered_links = [base_url + link for link in filtered_links]
    with open("developer_and_userguide_links.json", "w") as _file:
        json.dump(filtered_links, _file, indent=4)
    print(f"{len(filtered_links)=}")
    return list(set(filtered_links))


# TOC to find all the user guide HTML links
def get_toc(links: List[str]) -> List[Dict]:
    for link in links:
        url = link + "toc-contents.json"
        print(f"{url=}")
        response = requests.get(url)
        # link looks something like this 'https://docs.aws.amazon.com/lambda/latest/dg/toc-contents.json'
        service = link.split("/")[3]
        with open(f"toc/{service}.json", "w") as _file:
            json.dump(
                {
                    "base_url": link,
                    "service": service,
                    "toc": json.loads(response.text),
                },
                _file,
                indent=4,
            )
            print(f"{service} toc downloaded")

def extract_hrefs(data):
    hrefs = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'href':
                hrefs.append(value)
            else:
                hrefs.extend(extract_hrefs(value))
    elif isinstance(data, list):
        for item in data:
            hrefs.extend(extract_hrefs(item))
    return hrefs

def sanitize_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):  # remove all javascript and stylesheet code
        script.extract()
    return str(soup)

def run():
    links = get_href_links("https://docs.aws.amazon.com/en_us/main-landing-page.xml")
    valid_xml_pages = get_valid_xml_links(links)
    devloper_and_ug_links = get_developer_and_user_guide_links(valid_xml_pages)
    get_toc(devloper_and_ug_links)

    toc_path = pathlib.Path("toc")
    for path in toc_path.iterdir():
        with open(path, "r") as _file:
            data = json.load(_file)
            hrefs = extract_hrefs(data['toc'])
            print(hrefs)
            for href in hrefs:
                response = requests.get(data["base_url"] + href)
                markdown = md(sanitize_html(response.text))
                service_dir = pathlib.Path("markdown_doc") / data["service"]
                service_dir.mkdir(parents=True, exist_ok=True)
                with open(
                    service_dir / f"{pathlib.Path(href).name}.md", "w"
                ) as md_file:
                    md_file.write(markdown)


if __name__ == "__main__":
    run()
