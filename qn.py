import base64
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import string
import subprocess
import sys
import tempfile
from typing import Optional

import toml
import typer
from cryptography.fernet import Fernet, InvalidToken
from jsondb import jsondb
from rich import print
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

app = typer.Typer()
app_locked = typer.Typer()
db = None

date_format = "%a %d %b %Y %X"
SEPERATOR = "+++"


class RichStyles:
    title = Style(color="green", bold=True)
    tag = Style(color="black", bgcolor="blue")


class Paths:
    note_root = pathlib.Path.home() / ".local/qn/"
    note_path = pathlib.Path.home() / ".local/qn/qn.json"
    enc_path = pathlib.Path.home() / ".local/qn/qn.enc"


def environ_present(key="EDITOR"):
    return key in os.environ


def open_temp_md_file(
    title="",
    tags=[],
    created_date=datetime.datetime.now().strftime(date_format),
    mdtext="",
):
    command = string.Template("$editor $filename")
    if environ_present("EDITOR"):
        editor = os.environ["EDITOR"]
        fd, filename = tempfile.mkstemp(suffix=".md", text=True)
        with open(filename, "w") as file:

            file.write(
                "+++\n{}+++{}".format(
                    toml.dumps(
                        {
                            "title": title,
                            "tags": tags,
                            "created_date": created_date,
                        }
                    ),
                    mdtext,
                )
            )
        write_status = subprocess.call(
            command.substitute(editor=editor, filename=filename), shell=True
        )
        if write_status != 0:
            os.remove(filename)
        return filename, write_status
    else:
        raise Exception("EDITOR not found in env")


def parse_front_matter(filepath):
    filestr = ""
    with open(filepath, "r") as file:
        filestr = file.read()
    if filestr:
        strlist = filestr.split(SEPERATOR)
        if strlist and strlist[1]:
            try:
                fmdict = toml.loads(strlist[1])
                return fmdict
            except toml.TomlDecodeError as err:
                print(
                    "error encountered while decoding TOML string - {}".format(
                        str(filepath)
                    )
                )


def distinct_tags():
    tags = set()
    notes = db.find(lambda x: True)
    for note in notes:
        tags.update(note.get("tags"))
    return list(tags)


def distinct_titles():
    notes = db.find(lambda x: True)
    return [note.get("title") for note in notes]


def extract_md_text(filepath):
    filestr = ""
    with open(filepath, "r") as file:
        filestr = file.read()
    if filestr:
        strlist = filestr.split(SEPERATOR)
        if strlist and strlist[2]:
            return strlist[2]


def render_table(notes):
    table = Table("title", "tags", "created_date", title="quick notes", expand=True)
    for note in notes:
        # tags = note.get("tags")
        # colored_tags = ", ".join(map(lambda x: "[black on blue]#" + x + "[/]", tags))
        table.add_row(
            note.get("title"),
            ", ".join(note.get("tags")) or "-",
            note.get("created_date"),
        )
    print(table)


def display_notes(notes):
    for note in notes:
        tags = Text()
        for tag in note.get("tags"):
            tags.append("#{}".format(tag), style=RichStyles.tag)
            tags.append("  ")

        print(
            Panel(
                Markdown(note.get("note") or ">", code_theme="ansi_dark"),
                title=note.get("title"),
                title_align="center",
                subtitle=tags + Text(note.get("created_date")),
                subtitle_align="right",
            )
        )
        print("\n")


def filter_notes_by_tags(tags):
    return db.find(lambda x: set(tags).issubset(set(x.get("tags"))))


def get_all_notes_ordered(reverse=True):
    all_notes = db.find(lambda x: True)
    return sorted(
        all_notes,
        key=lambda i: datetime.datetime.strptime(i["created_date"], date_format),
        reverse=reverse,
    )


def fuzzy_search(options):
    fuzzy_search_command = string.Template(
        'echo -n "$options" | sk -m --color="prompt:27,pointer:27" --preview="qn preview {}" --preview-window=up:50%'
    )
    options = "\n".join(options)
    selected = subprocess.Popen(
        fuzzy_search_command.substitute(options=options),
        shell=True,
        stdout=subprocess.PIPE,
    ).communicate()[0]
    selected = selected.decode("utf-8")
    return list(filter(None, selected.split("\n")))


@app.command()
def preview(title: str):
    note = db.find(lambda x: x.get("title") == title)
    display_notes(note)


@app.command()
def today():
    title = datetime.datetime.now().strftime("%d%b%Y")
    note = db.find(lambda x: x.get("title") == title)
    if note:
        edit(title)
    else:
        filename, status = open_temp_md_file(title=title)
        front_matter = parse_front_matter(filename)
        db.insert(
            [{**parse_front_matter(filename), **{"note": extract_md_text(filename)}}]
        )
        print("[green]new note added")


@app.command()
def new(title: str):
    note = db.find(lambda x: x.get("title") == title)
    if note:
        edit(title)
    else:
        filename, status = open_temp_md_file(title=title)
        front_matter = parse_front_matter(filename)
        front_matter["title"] = front_matter["title"] or title
        db.insert(
            [{**parse_front_matter(filename), **{"note": extract_md_text(filename)}}]
        )
        print("[green]new note added")


@app.command()
def edit():
    def update(document):
        if document:
            filename, status = open_temp_md_file(
                note["title"], note["tags"], note["created_date"], mdtext=note["note"]
            )
            with open(filename, "r") as file:
                updated_front_matter = parse_front_matter(filename)
                updated_text = extract_md_text(filename)
                document.update(**updated_front_matter, **{"note": updated_text})
                return document

    title = fuzzy_search(distinct_titles())
    if title:
        note = db.find(lambda x: x.get("title") == title[0])
        if note:
            note = note[0]
            db.update(update, lambda x: x.get("title") == title[0])
        else:
            print("[red]no note found with this title")


@app.command()
def tag(tagstr: str):
    if tagstr:
        tags = list(map(str.strip, tagstr.split(",")))
        notes = filter_notes_by_tags(tags)
        (notes)
    else:
        tag = fuzzy_search(distinct_tags())
        if tag:
            notes = filter_notes_by_tags(tag)
            display_notes(notes)


@app.command()
def lss(order: str = typer.Argument("recent"), val: int = typer.Argument(5)):
    if order not in ["recent", "last"]:
        raise Exception('order has to be either "first" or "last"')
    all_notes = get_all_notes_ordered()
    if order == "first":
        render_table(all_notes[:val])
    else:
        render_table(all_notes[-val:])


@app.command()
def ls(order: str = typer.Argument("recent"), val: int = typer.Argument(5)):
    if order not in ["recent", "last"]:
        raise Exception('order has to be either "first" or "last"')
    all_notes = get_all_notes_ordered()
    notes = []
    if order == "first":
        display_notes(all_notes[:val])
    else:
        display_notes(all_notes[-val:])


@app.command()
def show():
    title = fuzzy_search(distinct_titles())
    if title:
        note = db.find(lambda x: x.get("title") == title[0])
        if note:
            display_notes(note)


@app.command()
def find(searchstr: str):
    searchstr = searchstr.strip()
    notes = db.find(lambda x: searchstr in x.get("title") or searchstr in x.get("note"))
    display_notes(notes)


@app.command()
def rm():
    title = fuzzy_search(distinct_titles())
    if title:
        deleted_doc = db.delete(lambda x: x.get("title") == title[0])
        if deleted_doc:
            print('[red]note "{}" deleted'.format(title[0]))


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
    with open(Paths.note_path, "r") as file:
        cipher_text = fernet.encrypt(file.read().encode("utf-8"))
    Paths.note_path.unlink()
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
        with open(Paths.note_path, "w") as file:
            file.write(plain_text.decode("utf-8"))
        Paths.enc_path.unlink()
    except InvalidToken as e:
        print("[red]invalid password")


@app.command()
@app_locked.command()
def export(path: str):
    pass


def run():
    if not shutil.which("sk"):
        print("[bold red]could not find sk in path")
        print("install from https://github.com/lotabout/skim")
    if not Paths.enc_path.exists():
        global db
        db = jsondb(str(Paths.note_path))
        db.set_index("title")
        app()
    else:
        app_locked()
    Paths.note_root.mkdir(parents=True, exist_ok=True)
