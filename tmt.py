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
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.markdown import Markdown

app = typer.Typer()

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
            toml.dump(template, file)
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
