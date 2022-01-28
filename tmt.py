import datetime
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


class RichStyles:
    backlog = Style(color="black", bgcolor="dark_orange3")
    selected = Style(color="black", bgcolor="blue")
    running = Style(color="black", bgcolor="green")
    done = Style(color="black", bgcolor="grey30")
    revisit = Style(color="black", bgcolor="light_goldenrod1")
    date = Style(color="grey70")
    tag_style = Style(color="black", bgcolor="blue")
    title_style = Style(color="green", bold=True)
    timeframe = Style(color="blue")
    NA = Style(color="grey42")
    days_overdue = Style(color="red")
    days_left = Style(color="green")
    total = Style(color="black", bgcolor="grey93")
    summary_title = Style(color="green", bold=True)
    empty = Style(color="white", bgcolor="black")

    @staticmethod
    def get_style(style):
        return getattr(RichStyles, style)


class RichTable:
    task = "task"
    status = "status"
    tag = "tag"
    tags = "tags"
    target_date = "target_date"
    days_left = "days_left"
    start_date = "start_date"
    timeframe = "timeframe"
    NA = "NA"

    @staticmethod
    def get_table(table):
        if table == "date_table":
            return Table(
                expand=True,
                box=box.ROUNDED,
                show_lines=True,
                show_header=False,
            )
        elif table == "task_table":
            return Table(
                RichTable.task,
                RichTable.status,
                RichTable.tags,
                RichTable.target_date,
                RichTable.days_left,
                expand=True,
                leading=1,
            )
        elif table == "initial_summary":
            return Table(
                *[
                    Column(state, style=RichStyles.get_style(state))
                    for state in states.possible_states()
                ],
                title="status summary",
                expand=True,
            )
        else:
            return None


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


def display_task(task):
    console = Console(color_system="256")
    tags = Text()
    for tag in task.get("tags"):
        tags.append("#{}".format(tag), style=RichStyles.tag_style)
        tags.append(" ── ")

    start_date, target_date = task.get("start_date"), task.get("target_date")
    table = Text()
    if start_date and target_date:
        table = RichTable.get_table("date_table")
        days_left = str(find_days_left(task))
        table.add_row(
            Text(RichTable.start_date, style=RichStyles.date),
            task.get("start_date"),
            Text(RichTable.target_date, style=RichStyles.date),
            task.get("target_date"),
        )
        table.add_row(
            Text(RichTable.timeframe, style=RichStyles.timeframe),
            str(find_timeframe(task)),
            Text(RichTable.days_left, style=RichStyles.date),
            stylize_days_left(str(find_days_left(task))),
        )
    print("\n")
    console.print(
        Panel(
            Group(
                Text("\n" + task.get("task") + "\n", style="yellow", justify="center"),
                table,
                Markdown(task.get("description"), code_theme="ansi_dark"),
            ),
            title="[{}]{}[/]".format(
                str(getattr(RichStyles, task.get("status"))), task.get("status")
            ),
            title_align="left",
            subtitle=tags + Text(task.get("created_date")),
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
    return Text(days_left, style=style)


def render_table(tasks):
    table = RichTable.get_table("task_table")
    for task in tasks:
        status = task.get("status")
        table.add_row(
            task.get("task"),
            Text(status, style=RichStyles.get_style(status)),
            ", ".join(task.get("tags")),
            task.get("target_date") or Text(RichTable.NA, style=RichStyles.NA),
            stylize_days_left(str(find_days_left(task))),
        )
    print(table)


def open_temp_toml_file(template=None):
    if not template:
        template = {
            "-": [
                {
                    "task": "",
                    "status": "",
                    "tags": [],
                    "start_date": "",
                    "target_date": "",
                    "description": "\n",
                }
            ]
        }
    command = string.Template("$editor $filename")
    if not "EDITOR" in os.environ:
        raise Exception("EDITOR not found in env")
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
        return {}
    else:
        return task


def prepare_task_for_insert(task):
    start_date, target_date = process_date_for_insert(task)
    if start_date or target_date:
        task.update(
            {
                "start_date": start_date,
                "target_date": target_date,
            }
        )
    else:
        task.pop("start_date")
        task.pop("target_date")
    task.update({"created_date": datetime.datetime.now().strftime(date_format)})
    return task


def parse_start_and_target_date(task):
    start_date, target_date = task.get("start_date"), task.get("target_date")
    try:
        target_date = dtparser.parse(target_date).date()
        start_date = dtparser.parse(start_date).date()
    except dtparser.ParserError:
        print("error in parsing dates!!")
        sys.exit()
    return start_date, target_date


def process_date_for_insert(task):
    start_date, target_date = task.get("start_date", ""), task.get("target_date", "")

    if start_date and target_date:
        start_date, target_date = parse_start_and_target_date(task)
        if start_date > target_date:
            print("[red]start_date need to be lesser than target_date")
            sys.exit(0)
        else:
            return start_date.strftime(date_format), target_date.strftime(date_format)
    elif target_date and not start_date:
        try:
            target_date = dtparser.parse(target_date).date()
            start_date = (
                dtparser.parse(task.get("created_date")).date()
                if task.get("created_date")
                else datetime.datetime.now().date()
            )
            return start_date.strftime(date_format), target_date.strftime(date_format)
        except dtparser.ParserError:
            print("error in parsing dates!!")
            sys.exit()
    else:
        return "", ""


def find_timeframe(task):
    if task.get("start_date") and task.get("target_date"):
        start_date, target_date = parse_start_and_target_date(task)
        return (target_date - start_date).days
    return "NA"


def find_days_left(task):
    if task.get("start_date") and task.get("target_date"):
        start_date, target_date = parse_start_and_target_date(task)
        today = datetime.datetime.now().date()
        if start_date > today:
            return "task start date has not reached"
        else:
            return (target_date - today).days
    return "NA"


def insert(tasks):
    total_tasks = len(tasks.get("-"))
    insert_count = 0
    for task in tasks.get("-"):
        task_name = task.get("task")
        task = validate_task(task)
        if task:
            task = prepare_task_for_insert(task)
            print(task)
            try:
                db.insert([task])
                insert_count += 1
            except DuplicateEntryError as err:
                print("[red]Duplicate task found - {}".format(task_name))
    print("[green bold]{}/{} task(s) added".format(insert_count, total_tasks))


def filter_tasks_by_tags(tagstr: str):
    tags = list(map(str.strip, tagstr.split(",")))
    return db.find(
        lambda x: set(tags).issubset(set(x.get("tags"))) and x.get("archived") != True
    )


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
    all_tasks = get_all_tasks()
    return sorted(
        all_tasks,
        key=lambda i: dtparser.parse(i["created_date"]),
        reverse=reverse,
    )


def get_distinct_tags():
    tags = set()
    all_tasks = get_all_tasks()
    for task in all_tasks:
        tags.update(task.get("tags"))
    return tags


def get_all_task_name():
    all_tasks = get_all_tasks()
    return [task["task"] for task in all_tasks]


def display_initial_summary(total_task, tasknumber_by_status):
    print(
        Text(
            "total number of tasks {}".format(total_task),
            style=RichStyles.summary_title,
            justify="center",
        )
    )
    print("\n")
    table = RichTable.get_table("initial_summary")
    rows = [tasknumber_by_status.get(state) for state in states.possible_states()]
    table.add_row(*list(map(str, rows)))
    print(table)


def display_tag_based_summary(distinct_tags):
    table = RichTable.get_table("tag_summary")
    renderables = list()
    for state in states.possible_states():
        tasks = filter_tasks_by_status(state)
        tags = list()
        for task in tasks:
            tags.extend(task.get("tags"))
        if tags:
            content = Text("\n")
            for tag, number in Counter(tags).items():
                content += Text(" {} ".format(tag), style=RichStyles.tag_style)
                content += Text(
                    " {} ".format(str(number)), style=RichStyles.total
                ) + Text("\n")
            renderables.append(
                Panel(
                    content,
                    title="[{}] {} [/]".format(str(RichStyles.get_style(state)), state),
                )
            )
    print("\n")
    print(Columns(renderables, equal=True, align="center"))


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
def tag(tagstr: str):
    tasks = filter_tasks_by_tags(tagstr)
    render_table(tasks)


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
    tasknumber_by_status = Counter({})
    total_tasks += get_total_number_of_tasks()
    tasknumber_by_status += Counter(number_of_task_based_on_status())
    display_initial_summary(total_tasks, tasknumber_by_status)
    distinct_tags = get_distinct_tags()
    display_tag_based_summary(distinct_tags)


@app.command()
def ll(limit: int = typer.Argument(5)):
    all_tasks = get_all_tasks_ordered()
    tasks = all_tasks[:limit]
    if limit < 0:
        tasks = all_tasks[limit:]
    if tasks:
        for task in tasks:
            display_task(task)


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


def run():
    if not Paths.enc_path.exists():
        global db
        db = jsondb(str(Paths.tmt_path))
        db.set_index("task")
        app()
    else:
        app_locked()
    Paths.tmt_root.mkdir(parents=True, exist_ok=True)
