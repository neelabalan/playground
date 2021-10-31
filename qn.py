import pathlib
import datetime
import sys
import os
import subprocess
import string
import json

import typer
import toml
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.markdown import Markdown

app = typer.Typer()

command = string.Template("$editor $filename")

console = Console()

note_root = pathlib.Path.home() / "qn"
note_root.mkdir(parents=True, exist_ok=True)

date_format = "%a %d %b %Y %X"

template = "---\n{}---"

tag_style = Style(color="black", bgcolor="blue")
title_style = Style(color="green", bold=True)


def environ_present(key="EDITOR"):
    return key in os.environ


def diplay_note(front_matter, mdtext):
    tags = Text()
    for tag in front_matter.get("tags"):
        tags.append("#{}".format(tag), style=tag_style)
        tags.append("  ")

    console.print(
        Panel(
            Markdown(mdtext, code_theme='ansi_dark'),
            title=front_matter.get("title"),
            title_align="center",
            subtitle=tags + Text(front_matter.get("created_date")),
            subtitle_align="right",
        )
    )


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
                return toml.loads(strlist[1])
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
    return notesmeta


@app.command()
def new(title: str = typer.Argument(datetime.datetime.now().strftime("%Y-%m-%d"))):
    filename, status = open_temp_md_file(title)


@app.command()
def tag(tagstr: str):
    tags = list(map(str.strip, tagstr.split(",")))
    metadata = notes_meta_data()
    for notepath, data in metadata.items():
        if set(tags).issubset(set(data.get("tags"))):
            diplay_note(data, extract_md_text(notepath))


@app.command()
def ls():
    pass

@app.command()
def find(searchstr: str):
    pass

if __name__ == "__main__":
    app()
