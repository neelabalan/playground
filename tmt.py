import pathlib
import datetime
import sys
import os
import subprocess
import string
import json
import tempfile

from jsondb import jsondb

import typer
import toml
from toml.encoder import _dump_str, TomlEncoder, unicode

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.markdown import Markdown

app = typer.Typer()
edit_app = typer.Typer()
app.add_typer(edit_app, name='edit')

command = string.Template("$editor $filename")

console = Console()

task_root = pathlib.Path.home() / "qn"
task_root.mkdir(parents=True, exist_ok=True)

date_format = "%a %d %b %Y %X"

template = {"-": [{"task": "", "description": "", "status": "", "tags": []}]}

tag_style = Style(color="black", bgcolor="blue")
title_style = Style(color="green", bold=True)


class states:
    BACKLOG = "backlog"
    SELECTED = "selected"
    RUNNING = "running"
    DONE = "done"
    REVISIT = "revisit"

    def possible_states():
        return (
            states.BACKLOG,
            states.DONE,
            states.REVISIT,
            states.RUNNING,
            states.SELECTED,
        )

# https://github.com/sanskrit-coders/sanskrit_data/blob/67e0999be6f8bf7fff761f0484141e03b9e551f4/sanskrit_data/toml_helper.py

def _dump_str_prefer_multiline(v):
  multilines = v.split('\n')
  if len(multilines) > 1:
    return unicode('"""\n' + v.replace('"""', '\\"""').strip() + '\n"""')
  else:
    return _dump_str(v)


class MultilinePreferringTomlEncoder(TomlEncoder):
  def __init__(self, _dict=dict, preserve=False):
    super(MultilinePreferringTomlEncoder, self).__init__(_dict=dict, preserve=preserve)
    self.dump_funcs[str] = _dump_str_prefer_multiline


def get_status_styled(status):
    color_map = {
        states.BACKLOG: "black on dark_orange3",
        states.SELECTED: "black on blue",
        states.RUNNING: "black on green",
        states.DONE: "black on grey58",
        states.REVISIT: "black on light_goldenrod1",
    }
    return "[{}] {} [/]".format(color_map.get(status), status)


def environ_present(key="EDITOR"):
    return key in os.environ


def construct_title(_id, task, status):
    return (
        "[black on grey93] {} [/] ────".format(_id)
        + task
        + "──── "
        + get_status_styled(status)
    )


def display_task(task):
    tags = Text()
    for tag in task.get("tags"):
        tags.append("#{}".format(tag), style=tag_style)
        tags.append("  ")

    console.print(
        Panel(
            Markdown(task.get("description"), code_theme="ansi_dark"),
            title=construct_title(
                task.get("_id"), task.get("task"), task.get("status")
            ),
            title_align="center",
            subtitle=tags + Text(task.get("created_date")),
            subtitle_align="right",
            padding=1,
        )
    )


def open_temp_toml_file(template=template):
    if environ_present("EDITOR"):
        editor = os.environ["EDITOR"]
        fd, filename = tempfile.mkstemp(suffix=".toml", text=True)
        with open(filename, "w") as file:
            toml.dump(template, file, encoder=MultilinePreferringTomlEncoder())
        write_status = subprocess.call(
            command.substitute(editor=editor, filename=filename), shell=True
        )
        if write_status != 0:
            os.remove(filename)
        return filename, write_status
    else:
        raise Exception("EDITOR not found in env")


def insert(tasks):
    total_tasks = len(tasks.get("-"))
    insert_count = 0
    for task in tasks.get("-"):
        task_name = task.get("task")
        if not task:
            console.print("[red bold]task not added")
            sys.exit()
        if not task.get("status") in states.possible_states():
            console.print(
                "[red bold]state has be any one of {}".format(states.possible_states())
            )
            sys.exit()
        try:
            db.insert(
                [
                    {
                        "task": task_name,
                        "status": task.get("status"),
                        "description": task.get("description"),
                        "tags": task.get("tags"),
                        "created_date": task.get("added_date")
                        or datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
                    }
                ]
            )
            insert_count += 1
        except DuplicateEntryError as err:
            console.print("[red]Duplicate task found - {}".format(task_name))
    console.print(
        "[green bold]{}/{} {} added".format(
            insert_count,
            total_tasks,
            "task" if total_tasks == 1 else "tasks",
        )
    )


@app.command()
def new():
    filename, status = open_temp_toml_file()
    total_bookmarks = 0
    if status == 0:
        with open(filename, "r") as file:
            tasks = toml.load(file)
            insert(tasks)


@app.command()
def tag(tagstr: str):
    tags = list(map(str.strip, tagstr.split(",")))
    tasks = db.find(lambda x: set(tags).issubset(set(x.get("tags"))))
    for task in tasks:
        display_task(task)


@edit_app.command("id")
def edit_id(_id: int):
    def update(document):
        if document:
            filename, status = open_temp_toml_file(
                {
                    "task": document.get("task"),
                    "status": document.get("status"),
                    "tags": document.get("tags"),
                    "description": document.get("description"),
                }
            )
            if status == 0:
                with open(filename, "r") as file:
                    updated_task = toml.load(file)
                    document.update(updated_task)
                    return document
    db.update(update, lambda x: x.get("_id") == _id)


@edit_app.command("tag")
def edit_tag(tag: str):
    pass



@app.command()
def rm(id: str):
    pass


@app.command()
def summary():
    pass


@app.command()
def ls():
    pass


@app.command()
def lss():
    pass


@app.command()
def find(searchstr: str):
    pass


def init_db():
    dbroot = pathlib.Path.home() / ".local/tmt"
    dbroot.mkdir(parents=True, exist_ok=True)
    db = jsondb(str(pathlib.Path(dbroot / "tmt.json")))
    db.set_index("task")
    db.set_index("_id")
    return db


db = init_db()
if __name__ == "__main__":
    app()
