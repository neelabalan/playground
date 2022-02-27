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
from collections import Counter
from typing import Optional

import dateutil.parser as dtparser
import pyskim
import toml
import typer
from cryptography.fernet import Fernet, InvalidToken
from jsondb import DuplicateEntryError, jsondb
from rich import box, print
from rich.columns import Columns
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.table import Column, Table
from rich.text import Text
from toml.encoder import TomlEncoder, _dump_str, unicode

app = typer.Typer()
app_locked = typer.Typer()

date_format = "%d%b%Y"
db = None


class states:
    BACKLOG = "backlog"
    SELECTED = "selected"
    RUNNING = "running"
    DONE = "done"
    REVISIT = "revisit"

    @staticmethod
    def possible_states():
        return (
            states.RUNNING,
            states.SELECTED,
            states.BACKLOG,
            states.DONE,
            states.REVISIT,
        )


class Paths:
    tmt_root = pathlib.Path.home() / ".local/tmt/"
    tmt_path = pathlib.Path.home() / ".local/tmt/tmt.json"
    enc_path = pathlib.Path.home() / ".local/tmt/tmt.enc"


class Color:
    white = "grey93"
    black = "black"

    class Light:
        grey = "grey27"
        red = "red"
        green = "green"
        blue = "blue"
        yellow = "yellow"

    class Dark:
        sky_blue = "deep_sky_blue4"
        orange = "orange4"
        blue = "dark_blue"
        green = "dark_green"
        red = "dark_red"
        grey = "grey11"


class RichStyles:
    class Status:
        backlog = Style(bgcolor=Color.Dark.blue)
        selected = Style(bgcolor=Color.Dark.sky_blue)
        running = Style(bgcolor=Color.Dark.green)
        done = Style(bgcolor=Color.Dark.grey)
        revisit = Style(bgcolor=Color.Dark.orange)

    tag_style = Style(color=Color.Light.blue, bold=True)
    title_style = Style(color=Color.Light.green, bold=True)

    NA = Style(color=Color.Light.grey)
    days_overdue = Style(bgcolor=Color.Dark.red)
    days_left = Style(bgcolor=Color.Dark.green)
    date_text = style = Style(bgcolor=Color.Dark.grey)

    date = style = Style(bgcolor=Color.Light.grey)
    total = Style(bgcolor=Color.Light.grey)
    summary_title = Style(color=Color.Light.green, bold=True)
    priority = {
        1: Style(bgcolor=Color.Dark.red),
        2: Style(bgcolor=Color.Dark.orange),
        3: Style(bgcolor=Color.Dark.green),
        4: Style(bgcolor=Color.Dark.sky_blue),
        5: Style(bgcolor=Color.Dark.blue),
    }


class RichTable:
    task = "task"
    priority = "priority"
    status = "status"
    tag = "tag"
    tags = "tags"
    due_date = "due date"
    days_left = "days left"
    NA = "NA"


class MultilinePreferringTomlEncoder(TomlEncoder):
    def __init__(self, _dict=dict, preserve=False):
        super(MultilinePreferringTomlEncoder, self).__init__(
            _dict=dict, preserve=preserve
        )
        self.dump_funcs[str] = MultilinePreferringTomlEncoder._dump_str_prefer_multiline

    # https://github.com/sanskrit-coders/sanskrit_data/blob/67e0999be6f8bf7fff761f0484141e03b9e551f4/sanskrit_data/toml_helper.py
    @staticmethod
    def _dump_str_prefer_multiline(v):
        multilines = v.split("\n")
        if len(multilines) > 1:
            return unicode('"""\n' + v.replace('"""', '\\"""').strip() + '\n"""')
        else:
            return _dump_str(v)


def display_task(task):
    console = Console(color_system="256")
    tags = Text()
    for tag in task.get("tags"):
        tags.append(" #{} ".format(tag), style=RichStyles.tag_style)
        tags.append(" ── ")

    due_date = task.get("due_date")
    subtitle = Text("")
    if due_date:
        subtitle = (
            tags
            + Text(" days left ", style=RichStyles.date_text)
            + stylize_days_left(" {} ".format(str(find_days_left(task))))
            + Text(" ── ")
            + Text(" due date ", style=RichStyles.date_text)
            + Text(" {} ".format(due_date), style=RichStyles.date)
            + Text(" ── ")
            + Text(" created date ", style=RichStyles.date_text)
            + Text(" {} ".format(task.get("created_date")), style=RichStyles.date)
        )
    else:
        subtitle = (
            tags
            + Text(" created date ", style=RichStyles.date_text)
            + Text(" {} ".format(task.get("created_date")), style=RichStyles.date)
        )
    print("\n")
    console.print(
        Panel(
            Group(
                Text("\n" + task.get("task") + "\n", style="yellow", justify="center"),
                Markdown(task.get("description"), code_theme="ansi_dark"),
                Text("\n"),
            ),
            title="[{}] {} [/]".format(
                str(getattr(RichStyles.Status, task.get("status"))), task.get("status")
            ),
            title_align="left",
            subtitle=subtitle,
            subtitle_align="right",
        )
    )
    print("\n")


def stylize_days_left(days_left):
    if "-" in days_left:
        style = RichStyles.days_overdue
    elif "NA" == days_left:
        style = RichStyles.NA
    else:
        style = RichStyles.days_left
    return Text(days_left, style=style, justify="center")


def render_table(tasks):
    table = Table(
        RichTable.priority,
        RichTable.task,
        RichTable.status,
        RichTable.tags,
        RichTable.due_date,
        RichTable.days_left,
        expand=True,
        leading=1,
    )
    for task in tasks:
        status = task.get("status")
        table.add_row(
            Text(
                str(task.get("priority")),
                style=RichStyles.priority.get(task.get("priority")),
                justify="center",
            ),
            task.get("task"),
            Text(status, style=getattr(RichStyles.Status, status)),
            ", ".join(task.get("tags")),
            task.get("due_date") or Text(RichTable.NA, style=RichStyles.NA),
            stylize_days_left(str(find_days_left(task))),
        )
    print(table)


def open_temp_toml_file(template=None):
    if not template:
        template = {
            "-": [
                {
                    "task": "",
                    "priority": 5,
                    "status": "",
                    "tags": [],
                    "due_date": "",
                    "description": "\n",
                }
            ]
        }
    fd, filename = tempfile.mkstemp(suffix=".toml", text=True)
    with open(filename, "w") as file:
        toml.dump(template, file, encoder=MultilinePreferringTomlEncoder())
    write_status = subprocess.call("$EDITOR {}".format(filename), shell=True)
    return filename, write_status


def validate_task(task):
    task_name = task.get("task")
    if not task:
        print("[red bold]task not added")
        return {}
    if not task_name:
        print("[red bold]task has no name")
        return {}
    if not task.get("status"):
        task["status"] = "backlog"
    if task.get("status") and task.get("status") not in states.possible_states():
        print("[red bold]state has be any one of {}".format(states.possible_states()))
        print("[red bold]proceeding with state as BACKLOG")
        task["status"] = "backlog"
    if task.get("priority") or task.get("priority") == 0:
        try:
            priority = int(task.get("priority"))
            if not 0 < priority < 6:
                print("[red bold]priority must be between [1,5]")
                print("[red bold]proceeding with priority as 5")
                priority = 5
            task["priority"] = priority
        except ValueError as err:
            print("[red]priority has to be a number")
            return {}

    due_date = process_date_for_insert(task)
    if due_date:
        task.update({"due_date": due_date})
    else:
        if task.get("due_date"):
            task.pop("due_date")
    if not task.get("created_date"):
        task.update({"created_date": datetime.datetime.now().strftime(date_format)})
    return task


def parse_due_date(task):
    due_date = task.get("due_date")
    try:
        due_date = dtparser.parse(due_date).date()
    except dtparser.ParserError:
        print("error in parsing due date!")
        sys.exit()
    return due_date


def process_date_for_insert(task):
    due_date = task.get("due_date", "")
    if due_date:
        due_date = parse_due_date(task)
        return due_date.strftime(date_format)
    else:
        return ""


def find_days_left(task):
    if task.get("due_date"):
        due_date = parse_due_date(task)
        today = datetime.datetime.now().date()
        return (due_date - today).days
    else:
        return "NA"


def insert(tasks):
    total_tasks = len(tasks.get("-"))
    insert_count = 0
    for task in tasks.get("-"):
        task_name = task.get("task")
        task = validate_task(task)
        if task:
            try:
                db.insert([task])
                insert_count += 1
            except DuplicateEntryError as err:
                print("[red]Duplicate task found - {}".format(task_name))
    print("[green bold]{}/{} task(s) added".format(insert_count, total_tasks))


def filter_tasks_by_status(status):
    return db.find(lambda x: x.get("status") == status and x.get("archived") != True)


def number_of_task_based_on_status():
    return {
        status: len(filter_tasks_by_status(status))
        for status in states.possible_states()
    }


def get_all_tasks():
    return db.find(lambda x: x.get("archived") != True)


def get_total_number_of_tasks():
    return len(get_all_tasks())


def get_all_tasks_ordered(reverse=True):
    return sorted(
        get_all_tasks(),
        key=lambda i: dtparser.parse(i["created_date"]),
        reverse=reverse,
    )


def get_distinct_tags():
    tags = set()
    all_tasks = get_all_tasks()
    for task in all_tasks:
        tags.update(task.get("tags"))
    return sorted(tags)


def get_all_task_name():
    all_tasks = get_all_tasks_ordered()
    return [task["task"] for task in all_tasks]


def display_summary(total_task, tasknumber_by_status):
    table = Table(
        "state",
        "tag",
        "total",
        "percentage",
        title="total number of tasks {}".format(total_task),
        padding=4,
    )
    print("\n")
    for state in states.possible_states():
        tasks = filter_tasks_by_status(state)
        tags = list()
        for task in tasks:
            tags.extend(task.get("tags"))
        if tags:
            content = Text("")
            tag_table = Table(
                box=None,
                show_header=False,
                show_edge=False,
                show_footer=False,
                expand=True,
            )
            for tag, number in Counter(tags).items():
                tag_table.add_row(tag, str(number))
        else:
            tag_table = Table()
        table.add_row(
            state,
            tag_table,
            str(tasknumber_by_status.get(state)),
            "{:.2f}%".format((tasknumber_by_status.get(state) / total_task) * 100),
            style=getattr(RichStyles.Status, state),
        )
    console = Console()
    console.print(table, justify="center")


@app.command()
def preview(task_name: str):
    task = db.find(lambda x: x.get("task") == task_name)
    display_task(task[0])


@app.command()
def new():
    filename, status = open_temp_toml_file()
    total_bookmarks = 0
    if status == 0:
        with open(filename, "r") as file:
            tasks = toml.load(file)
            insert(tasks)


@app.command()
def tag():
    tags = pyskim.skim(get_distinct_tags(), '-m --color="prompt:27,pointer:27"')
    if tags:
        tasks = db.find(lambda x: set(tags).issubset(set(x.get("tags"))))
        task_names = [task["task"] for task in tasks]
        task = pyskim.skim(
            task_names,
            '-m --color="prompt:27,pointer:27" --preview="tmt preview {}" --preview-window=up:50%',
        )
        if task:
            display_task(task[0])


@app.command()
def status(status: str = typer.Argument(states.RUNNING)):
    tasks = filter_tasks_by_status(status)
    if tasks:
        render_table(tasks)


def diff(prev_tasks, new_tasks):
    diff_dict = dict()
    for _id, task in new_tasks.items():
        if prev_tasks.get(_id) != task:
            diff_dict.update({_id: task})
            diff_dict.get(_id).update({"prev_task": prev_tasks.get(_id).get("task")})
    return diff_dict


@app.command()
def edit():
    task_names = pyskim.skim(
        get_all_task_name(),
        '-m --ansi --preview="tmt preview {}" --preview-window=up:50% --bind="ctrl-a:select-all"',
    )
    if not task_names:
        sys.exit()
    tasks = list()
    for task_name in task_names:
        tasks.extend(db.find(lambda x: x.get("task") == task_name))

    prev_tasks = {
        str(_id): {
            "task": task.get("task"),
            "status": task.get("status"),
            "tags": task.get("tags"),
            "description": task.get("description"),
            "due_date": task.get("due_date"),
        }
        for _id, task in enumerate(tasks, start=1)
    }
    filename, _ = open_temp_toml_file(prev_tasks)
    new_tasks = dict()
    with open(filename, "r") as file:
        new_tasks = toml.load(file)
    diff_dict = diff(prev_tasks, new_tasks)

    for _id, edited_task in diff_dict.items():
        prev_task = edited_task.pop("prev_task")

        def update(document):
            document.update(edited_task)
            return validate_task(document)

        db.update(update, lambda y: y.get("task") == prev_task)
    print("[green]{} task(s) updated".format(len(diff_dict)))


@app.command()
def rm():
    def update(document):
        if document:
            document.update({"archived": True})
            return document

    task_names = pyskim.skim(
        get_all_task_name(),
        '-m --ansi --preview="tmt preview {}" --preview-window=up:50%',
    )
    if task_names:
        count = 0
        for task_name in task_names:
            task = db.find(lambda x: x.get("task") == task_name)
            if task:
                db.update(update, lambda x: x.get("task") == task[0].get("task"))
                count += 1
        print("[green]{} task(s) archived".format(count))


@app.command()
def view():
    task_name = pyskim.skim(
        get_all_task_name(), '--ansi --preview="tmt preview {}" --preview-window=up:50%'
    )
    if task_name:
        task = db.find(lambda x: x.get("task") == task_name[0])
        if task:
            display_task(task[0])


@app.command()
def summary():
    total_tasks = 0
    tasknumber_by_status = Counter({state: 0 for state in states.possible_states()})
    total_tasks += get_total_number_of_tasks()
    tasknumber_by_status.update(Counter(number_of_task_based_on_status()))
    display_summary(total_tasks, tasknumber_by_status)


@app.command()
def ls(limit: int = typer.Argument(5)):
    all_tasks = get_all_tasks_ordered()
    tasks = all_tasks[:limit]
    if limit < 0:
        tasks = all_tasks[limit:]
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


@app.command()
def q():
    pass


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
    with open(Paths.tmt_path, "r") as file:
        cipher_text = fernet.encrypt(file.read().encode("utf-8"))
    Paths.tmt_path.unlink()
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
        with open(Paths.tmt_path, "w") as file:
            file.write(plain_text.decode("utf-8"))
        Paths.enc_path.unlink()
    except InvalidToken as e:
        print("[red]invalid password")


@app.command()
@app_locked.command()
def export(path: str):
    pass


def run():
    if not Paths.enc_path.exists():
        global db
        db = jsondb(str(Paths.tmt_path))
        db.set_index("task")
        app()
    else:
        app_locked()
    Paths.tmt_root.mkdir(parents=True, exist_ok=True)
