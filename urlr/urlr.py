import base64
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

import pyskim
import toml
import typer
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet, InvalidToken
from jsondb import DuplicateEntryError, jsondb
from rich import print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

app = typer.Typer()
app_locked = typer.Typer()
db = None


class RichStyles:
    title_style = Style(color="grey74", bold=True)
    url_style = Style(color="blue", underline=True)


class Paths:
    urlr_root = pathlib.Path.home() / ".local/urlr/"
    urlr_path = pathlib.Path.home() / ".local/urlr/urlr.json"
    enc_path = pathlib.Path.home() / ".local/urlr/urlr.enc"


def open_temp_toml_file(template={"-": [{"url": "", "title": "", "tags": []}]}):
    fd, filename = tempfile.mkstemp(suffix=".toml", text=True)
    with open(filename, "w") as file:
        toml.dump(template, file)
    write_status = subprocess.call("$EDITOR {}".format(filename), shell=True)
    return filename, write_status


def format_text(bookmark):
    newline = Text("\n\n", justify="center")
    bookmark_text = Text(justify="center")
    bookmark_text.append_text(Text(bookmark.get("title"), style=RichStyles.title_style))
    bookmark_text.append_text(newline)

    bookmark_text.append(Text(bookmark.get("url"), style=RichStyles.url_style))
    bookmark_text.append_text(newline)

    tags = bookmark.get("tags")
    colored_tags = map(lambda x: "[black on blue]#" + x + "[/]", tags)
    tags = " ── ".join(colored_tags)
    return Panel(
        bookmark_text,
        subtitle=tags,
        subtitle_align="right",
        padding=1,
    )


def display_bookmark(bookmarks):
    if bookmarks:
        for bookmark in bookmarks:
            print("\n\n")
            print(format_text(bookmark))


def get_website_title(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"
        },
    )
    web = BeautifulSoup(urllib.request.urlopen(request), features="html.parser")
    return web.title.string


def validate_insert(bookmark):
    url = bookmark.get("url")
    if not url:
        print("[red bold]url not added[/]")
        sys.exit()

    result = urllib.parse.urlparse(url)
    if not all([result.scheme, result.netloc]):
        print("[red bol]url not valid[/]")
        sys.exit()
    return bookmark


def insert(bookmarks):
    total_bookmark = len(bookmarks.get("-"))
    insert_count = 0
    for bookmark in bookmarks.get("-"):
        bookmark = validate_insert(bookmark)
        url = bookmark.get("url")
        try:
            db.insert(
                [
                    {
                        "url": url,
                        "title": bookmark.get("title")
                        or get_website_title(bookmark.get("url")),
                        "tags": bookmark.get("tags"),
                    }
                ]
            )
            insert_count += 1
        except DuplicateEntryError as err:
            console.print("[red]Duplicate url found - {}".format(url))
    print(
        "[green bold]{}/{} bookmark(s) added".format(
            insert_count,
            total_bookmark,
        )
    )


def get_bookmarks_sorted():
    all_bookmarks = db.find(lambda x: True)
    ordered_latest = sorted(
        all_bookmarks,
        key=lambda i: datetime.datetime.strptime(i["added_date"], date_format),
        reverse=True,
    )
    return ordered_latest


def distinct_tags():
    tags = list()
    urls = db.find(lambda x: True)
    for url in urls:
        tags.extend(url.get("tags"))
    return sorted(list(set(tags)))


def titles():
    notes = db.find(lambda x: True)
    return [note.get("title") for note in notes]


@app.command()
def new():
    filename, status = open_temp_toml_file()
    total_bookmarks = 0
    if status == 0:
        with open(filename, "r") as file:
            bookmarks = toml.load(file)
            insert(bookmarks)


@app.command()
def preview(title: str):
    console = Console(color_system="256")
    bookmark = db.find(lambda x: x.get("title") == title)
    if bookmark:
        console.print(format_text(bookmark[0]))


@app.command()
def tag():
    tags = pyskim.skim(distinct_tags(), '-m --color="prompt:27,pointer:27"')
    bookmarks = db.find(lambda x: set(tags).issubset(set(x.get("tags"))))
    titles = [bookmark["title"] for bookmark in bookmarks]
    bookmark = pyskim.skim(
        titles,
        '-m --color="prompt:27,pointer:27" --preview="urlr preview {}" --preview-window=up:50%',
    )
    display_bookmark(bookmark)


@app.command()
def find(searchstr: str):
    searchstr = searchstr.strip()
    bookmarks = db.find(
        lambda x: searchstr in x.get("title") or searchstr in x.get("url")
    )
    display_bookmark(bookmarks)


@app.command()
def ls(val: int = typer.Argument(10)):
    bookmarks = get_bookmarks_sorted()
    display_bookmark(bookmarks[:val])


@app.command()
def edit():
    title = pyskim.skim(
        title(),
        '-m --color="prompt:27,pointer:27" --preview="urlr preview {}" --preview-window=up:50%',
    )

    def update(document):
        if document:
            filename, status = open_temp_toml_file(
                {
                    "url": document.get("url"),
                    "title": document.get("title"),
                    "tags": document.get("tags"),
                }
            )
            if status == 0:
                with open(filename, "r") as file:
                    updated_bookmark = toml.load(file)
                    document.update(updated_bookmark)
                    return document

    db.update(update, lambda x: x.get("title") == title)


@app.command()
def rm():
    title = fuzzy_search(distinct_titles())
    doc = db.delete(lambda x: x.get("title") == title)
    return doc


@app.command("import")
def import_viv():
    fullpath = str(pathlib.Path.home()) + "/.config/vivaldi/Default/Bookmarks"
    bookmarks = {"-": list()}
    with open(fullpath) as browserbm:
        jsondict = json.loads(browserbm.read())
        blist = jsondict["roots"]["bookmark_bar"]["children"]
        for element in blist:
            print(element.get("name"))
            bookmarks["-"].append(
                {
                    "url": element.get("url"),
                    "title": element.get("name"),
                    "tags": ["browser"],
                }
            )
        insert(bookmarks)


@app.command()
def encrypt(
    password: str = typer.Option(
        ..., prompt=True, confirmation_prompt=True, hide_input=True
    )
):
    cipher_text = ""
    hasher = hashlib.sha3_256()
    hasher.update(password.encode("utf-8"))
    fernet = Fernet(base64.urlsafe_b64encode(hasher.digest()))
    with open(Paths.urlr_path, "r") as file:
        cipher_text = fernet.encrypt(file.read().encode("utf-8"))
    Paths.urlr_path.unlink()
    with open(Paths.enc_path, "w") as file:
        file.write(cipher_text.decode("utf-8"))


@app_locked.command()
def decrypt(password: str = typer.Option(..., prompt=True, hide_input=True)):
    cipher_text = plain_text = ""
    hasher = hashlib.sha3_256()
    hasher.update(password.encode("utf-8"))
    fernet = Fernet(base64.urlsafe_b64encode(hasher.digest()))
    with open(Paths.enc_path, "r") as file:
        cipher_text = file.read()
    try:
        plain_text = fernet.decrypt(cipher_text.encode("utf-8"))
        with open(Paths.urlr_path, "w") as file:
            file.write(plain_text.decode("utf-8"))
        Paths.enc_path.unlink()
    except InvalidToken as e:
        print("[red]invalid password")


@app.command()
@app_locked.command()
def export(path: str):
    pass


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        url_titles = pyskim.skim(
            titles(),
            '-m --color="prompt:27,pointer:27,marker:28" --preview="urlr preview {}" --preview-window=up:50%',
        )
        if url_titles:
            for title in url_titles:
                url = db.find(lambda x: x.get("title") == title)
                subprocess.call(
                    ["xdg-open", url[0].get("url")],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )


def run():
    if not Paths.enc_path.exists():
        global db
        db = jsondb(str(Paths.urlr_path))
        db.set_index("url")
        app()
    else:
        app_locked()
    Paths.urlr_root.mkdir(parents=True, exist_ok=True)
