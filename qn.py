import datetime
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
from jsondb import jsondb
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

app = typer.Typer()

command = string.Template("$editor $filename")

console = Console()

note_root = pathlib.Path.home() / ".local/qn/"
note_root.mkdir(parents=True, exist_ok=True)

date_format = "%a %d %b %Y %X"
SEPERATOR = "+++"
template = "+++\n{}+++{}"

title_style = Style(color="green", bold=True)
tag_style = Style(color="black", bgcolor="blue")


def environ_present(key="EDITOR"):
    return key in os.environ


def open_temp_md_file(
    title="",
    tags=[],
    created_date=datetime.datetime.now().strftime(date_format),
    mdtext="",
):
    if environ_present("EDITOR"):
        editor = os.environ["EDITOR"]
        fd, filename = tempfile.mkstemp(suffix=".md", text=True)
        with open(filename, "w") as file:

            file.write(
                template.format(
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
    console.print(table)


def display_notes(notes):
    for note in notes:
        tags = Text()
        for tag in note.get("tags"):
            tags.append("#{}".format(tag), style=tag_style)
            tags.append("  ")

        console.print(
            Panel(
                Markdown(note.get("note") or ">", code_theme="ansi_dark"),
                title=note.get("title"),
                title_align="center",
                subtitle=tags + Text(note.get("created_date")),
                subtitle_align="right",
            )
        )
        console.print("\n")


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
        console.print("[green]new note added")


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
        console.print("[green]new note added")


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
            console.print("[red]no note found with this title")


@app.command()
def tag(tagstr: str):
    if tagstr:
        tags = list(map(str.strip, tagstr.split(",")))
        notes = filter_notes_by_tags(tags)
        render_table(notes)
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
            console.print('[red]note "{}" deleted'.format(title[0]))


@app.command()
def export(path: str):
    """export to md"""
    pass


def init_db():
    db = jsondb(str(pathlib.Path(note_root / "qn.json")))
    db.set_index("title")
    return db


db = init_db()
if __name__ == "__main__":
    if not shutil.which("sk"):
        console.print("[bold red]could not find sk in path")
        console.print("install from https://github.com/lotabout/skim")
    else:
        app()
