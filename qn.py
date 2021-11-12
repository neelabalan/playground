import pathlib
import datetime
import sys
import os
import subprocess
import string
import json
from typing import Optional

import typer
import toml
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.markdown import Markdown
from rich.table import Table

app = typer.Typer()

command = string.Template("$editor $filename")

console = Console()

note_root = pathlib.Path.home() / "qn"
note_root.mkdir(parents=True, exist_ok=True)

date_format = "%a %d %b %Y %X"

template = "---\n{}---"

title_style = Style(color="green", bold=True)


def environ_present(key="EDITOR"):
    return key in os.environ


def open_temp_md_file(title):
    if environ_present("EDITOR"):
        editor = os.environ["EDITOR"]
        title = title.replace(" ", "_")
        filename = title + ".md"
        filepath = note_root / filename
        if not filepath.exists():
            with open(filepath, "w") as file:
                file.write(
                    template.format(
                        toml.dumps(
                            {
                                "title": title,
                                "tags": [],
                                "created_date": datetime.datetime.now().strftime(
                                    date_format
                                ),
                            }
                        )
                    )
                )
        write_status = subprocess.call(
            command.substitute(editor=editor, filename=str(filepath)), shell=True
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
        strlist = filestr.split("---")
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


def extract_md_text(filepath):
    filestr = ""
    with open(filepath, "r") as file:
        filestr = file.read()
    if filestr:
        strlist = filestr.split("---")
        if strlist and strlist[2]:
            return strlist[2]


def list_all_notes():
    notelist = []
    for file in pathlib.Path(note_root).iterdir():
        if file.is_file() and file.suffix == ".md":
            notelist.append(file)
    return notelist


def notes_meta_data():
    all_notes = list_all_notes()
    notesmeta = dict()
    for notepath in all_notes:
        notesmeta[str(notepath)] = parse_front_matter(notepath)
    return dict(
        sorted(
            notesmeta.items(),
            key=lambda item: datetime.datetime.strptime(
                item[1].get("created_date"), date_format
            ),
            reverse=True,
        )
    )


def render_table(metadata):
    table = Table("title", "tags", "created_date", title="quick notes", expand=True)
    for data in metadata.values():
        tags = data.get("tags")
        colored_tags = ", ".join(map(lambda x: "[black on blue]#" + x + "[/]", tags))
        table.add_row(
            data.get("title"),
            colored_tags or "-",
            data.get("created_date"),
        )
    console.print(table)


def get_distinct_tags():
    tags = set()
    metadata = notes_meta_data()
    for data in metadata.values():
        tags.update(data.get("tags"))
    return sorted(tags)


@app.command()
def new(title: str = typer.Argument(datetime.datetime.now().strftime("%Y-%m-%d"))):
    filename, status = open_temp_md_file(title)


@app.command()
def tag(tagstr: Optional[str] = typer.Argument(None)):
    if not tagstr:
        console.print("\n")
        console.print("\n".join(get_distinct_tags()))
    else:
        tags = list(map(str.strip, tagstr.split(",")))
        metadata = notes_meta_data()
        data_with_tags = dict()
        for notepath, data in metadata.items():
            if set(tags).issubset(set(data.get("tags"))):
                data_with_tags[notepath] = data
        render_table(data_with_tags)


@app.command()
def lss(order: str = typer.Argument("first"), val: int = typer.Argument(5)):
    if order not in ["first", "last"]:
        raise Exception('order has to be either "first" or "last"')
    metadata = list(notes_meta_data().items())
    if order == "first":
        render_table(metadata[:val])
    else:
        render_table(metadata[-val:])


@app.command()
def find(searchstr: str):
    searchstr = searchstr.strip()
    metadata = notes_meta_data()
    found_data = dict()
    for notepath, data in metadata.items():
        if searchstr in data.get("title"):
            found_data[notepath] = data
    render_table(found_data)


@app.command()
def edit():
    fuzzy_command = string.Template(
        "find $filepath -maxdepth 1 -type f -name *.md | fzf --preview-window=up:60% --preview='cat {}'"
    )
    response = subprocess.Popen(
        fuzzy_command.substitute(filepath=str(note_root)),
        shell=True,
        stdout=subprocess.PIPE,
    ).communicate()
    if response[0]:
        file = response[0].decode("utf-8").strip()
        subprocess.call("vim {}".format(file), shell=True)


if __name__ == "__main__":
    app()
