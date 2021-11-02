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
from rich.table import Table

app = typer.Typer()
edit_app = typer.Typer()
tag_app = typer.Typer()
status_app = typer.Typer()

app.add_typer(edit_app, name="edit")
app.add_typer(tag_app, name="tag")
app.add_typer(status_app, name="status")

command = string.Template("$editor $filename")

console = Console()

task_root = pathlib.Path.home() / "qn"
task_root.mkdir(parents=True, exist_ok=True)

date_format = "%a %d %b %Y %X"

template = {"-": [{"task": "", "status": "", "tags": [], "description": ""}]}

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


color_map = {
    states.BACKLOG: "black on dark_orange3",
    states.SELECTED: "black on blue",
    states.RUNNING: "black on green",
    states.DONE: "black on grey58",
    states.REVISIT: "black on light_goldenrod1",
}

# https://github.com/sanskrit-coders/sanskrit_data/blob/67e0999be6f8bf7fff761f0484141e03b9e551f4/sanskrit_data/toml_helper.py
def _dump_str_prefer_multiline(v):
    multilines = v.split("\n")
    if len(multilines) > 1:
        return unicode('"""\n' + v.replace('"""', '\\"""').strip() + '\n"""')
    else:
        return _dump_str(v)


class MultilinePreferringTomlEncoder(TomlEncoder):
    def __init__(self, _dict=dict, preserve=False):
        super(MultilinePreferringTomlEncoder, self).__init__(
            _dict=dict, preserve=preserve
        )
        self.dump_funcs[str] = _dump_str_prefer_multiline


def get_status_styled(status):
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
    console.print("\n\n")


def render_table(tasks):
    table = Table(
        "id", "task", "status", "tags", "created_date", title="tasks", expand=True
    )
    for task in tasks:
        status = task.get("status")
        table.add_row(
            str(task.get("_id")),
            task.get("task"),
            Text(status, style=color_map.get(status)),
            ", ".join(task.get("tags")),
            task.get("created_date"),
        )
    console.print(table)


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
                        "status": task.get("status") or states.BACKLOG,
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


def filter_tasks_by_tags(tagstr: str, status: str = typer.Argument("")):
    tags = list(map(str.strip, tagstr.split(",")))
    if not status:
        tasks = db.find(lambda x: set(tags).issubset(set(x.get("tags"))))
    else:
        tasks = db.find(
            lambda x: set(tags).issubset(set(x.get("tags")))
            and x.get("status") == status
        )
    return tasks


def fitler_tasks_by_status(status: str):
    return db.find(lambda x: x.get("status") == status)


@tag_app.command("brief")
def tag_brief(tagstr: str, status: str = typer.Argument("")):
    tasks = filter_tasks_by_tags(tagstr, status)
    render_table(tasks)


@tag_app.command("verbose")
def tag_verbose(tagstr: str, status: str = typer.Argument("")):
    tasks = filter_tasks_by_tags(tagstr, status)
    for task in tasks:
        display_task(task)


@status_app.command("brief")
def status_brief(status: str = typer.Argument(states.RUNNING)):
    tasks = fitler_tasks_by_status(status)
    render_table(tasks)


@status_app.command("verbose")
def status_brief(status: str = typer.Argument(states.RUNNING)):
    tasks = fitler_tasks_by_status(status)
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


def get_all_tasks_ordered():
    all_tasks = db.find(lambda x: True)
    return sorted(all_tasks, key=lambda i: i["created_date"], reverse=True)


@app.command("")
def ls(order: str = typer.Argument("recent"), limit: int = typer.Argument(5)):
    if not order in ("recent", "past"):
        console.print("[red]order has to be one of (recent | past)")
        sys.exit()

    all_tasks = get_all_tasks_ordered()
    if order == "recent":
        tasks = all_tasks[:limit]
    else:
        tasks = all_tasks[-limit:]

    if tasks:
        for task in tasks:
            display_task(task)


@app.command("")
def lss(order: str = typer.Argument("recent"), limit: int = typer.Argument(5)):
    if not order in ("recent", "past"):
        console.print("[red]order has to be one of (recent | past)")
        sys.exit()
    all_tasks = get_all_tasks_ordered()
    if order == "recent":
        tasks = all_tasks[:limit]
    else:
        tasks = all_tasks[-limit:]
    if tasks:
        render_table(tasks)


@app.command()
def find(searchstr: str):
    searchstr = searchstr.strip()
    tasks = db.find(
        lambda x: searchstr in x.get("task") or searchstr in x.get("description")
    )
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
