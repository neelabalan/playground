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
import toml
import typer
from jsondb import DuplicateEntryError, jsondb
from rich import box
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.table import Column, Table
from rich.text import Text
from toml.encoder import TomlEncoder, _dump_str, unicode

app = typer.Typer()
tag_app = typer.Typer()
inall_app = typer.Typer()

app.add_typer(tag_app, name="tag")
app.add_typer(inall_app, name="inall")

command = string.Template("$editor $filename")
fuzzy_search_command = string.Template(
    'echo -n "$options" | sk -m --color="prompt:27,pointer:27" --preview="tmt preview {}" --preview-window=up:50%'
)

console = Console()

task_root = pathlib.Path.home() / ".local/tmt/"
current_bucket_path = pathlib.Path.home() / ".local/tmt/current_bucket"
task_root.mkdir(parents=True, exist_ok=True)

date_time_format = "%a %d %b %Y %X"
date_format = "%d%b%Y"

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
            states.RUNNING,
            states.SELECTED,
            states.BACKLOG,
            states.DONE,
            states.REVISIT,
        )


color_map = {
    states.BACKLOG: "black on dark_orange3",
    states.SELECTED: "black on blue",
    states.RUNNING: "black on green",
    states.DONE: "black on grey30",
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


def display_task(task):
    tags = Text()
    for tag in task.get("tags"):
        tags.append("#{}".format(tag), style=tag_style)
        tags.append(" ── ")

    start_date, target_date = task.get("start_date"), task.get("target_date")
    table = Text()
    if start_date and target_date:
        table = Table(
            expand=True,
            box=box.ROUNDED,
            show_lines=True,
            show_header=False,
        )
        days_left = str(find_days_left(task))
        table.add_row(
            "[grey70]start_date",
            task.get("start_date"),
            "[grey70]target_date",
            task.get("target_date"),
        )
        table.add_row(
            "[grey70]timeframe",
            "[blue]" + str(find_timeframe(task)),
            "[grey70]days_left",
            stylize_days_left(str(find_days_left(task))),
        )
    console.print("\n")
    console.print(
        Panel(
            Group(
                Text("\n" + task.get("task") + "\n", style="yellow", justify="center"),
                table,
                Markdown(task.get("description"), code_theme="ansi_dark"),
            ),
            title=get_status_styled(task.get("status")),
            title_align="left",
            subtitle=tags + Text(task.get("created_date")),
            subtitle_align="right",
        )
    )

    console.print("\n")


def stylize_days_left(days_left):
    return "[{}]{}[/]".format("red" if "-" in days_left else "green", days_left)


def render_table(tasks, bucket_name=""):
    table = Table(
        "task",
        "status",
        "tags",
        "target_date",
        "days_left",
        title="{} tasks".format(bucket_name or str(bucket)),
        expand=True,
        leading=1,
    )
    for task in tasks:
        status = task.get("status")
        table.add_row(
            task.get("task"),
            Text(status, style=color_map.get(status)),
            ", ".join(task.get("tags")),
            task.get("target_date"),
            stylize_days_left(str(find_days_left(task))),
        )
    console.print(table)
    console.print("\n")


def render_in_all_table(alltasks):
    table = Table(
        "task",
        "status",
        "project",
        "tags",
        title="tasks",
        expand=True,
        leading=1,
    )
    for bucket, tasks in alltasks.items():
        for task in tasks:
            status = task.get("status")
            table.add_row(
                task.get("task"),
                Text(status, style=color_map.get(status)),
                bucket,
                ", ".join(task.get("tags")),
                task.get("created_date"),
            )
    console.print(table)
    console.print("\n")


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


def validate_task_insert(task):
    validation_pass = True
    task_name = task.get("task")
    if not task:
        console.print("[red bold]task not added")
        validation_pass = False
    elif not task_name:
        console.print("[red bold]task has no name")
        validation_pass = False
    elif task.get("status") and task.get("status") not in states.possible_states():
        console.print(
            "[red bold]state has be any one of {}".format(states.possible_states())
        )
        validation_pass = False
    else:
        pass
    return validation_pass


def parse_start_and_target_date(task):
    start_date, target_date = task.get("start_date"), task.get("target_date")
    try:
        target_date = dtparser.parse(target_date).date()
        start_date = dtparser.parse(start_date).date()
    except dtparser.ParserError:
        console.print("error in parsing dates!!")
        sys.exit()
    return start_date, target_date


def process_date_for_insert(task):
    start_date, target_date = task.get("start_date", ""), task.get("target_date", "")

    if start_date and target_date:
        start_date, target_date = parse_start_and_target_date(task)
        if start_date > target_date:
            console.print("[red]start_date need to be lesser than target_date")
            sys.exit(0)
        else:
            return start_date, target_date
    elif target_date and not start_date:
        try:
            target_date = dtparser.parse(target_date).date()
            start_date = (
                dtparser.parse(task.get("created_date")).date()
                if task.get("create_date")
                else datetime.datetime.now().date()
            )
            return start_date, target_date
        except dtparser.ParserError:
            console.print("error in parsing dates!!")
            sys.exit()
    else:
        return "", ""


def find_timeframe(task):
    start_date, target_date = parse_start_and_target_date(task)
    return (target_date - start_date).days


def find_days_left(task):
    start_date, target_date = parse_start_and_target_date(task)
    today = datetime.datetime.now().date()
    if start_date > today:
        return "task start date has not reached"
    else:
        return (target_date - today).days


def insert(tasks):
    total_tasks = len(tasks.get("-"))
    insert_count = 0
    for task in tasks.get("-"):
        task_name = task.get("task")
        validation_pass = validate_task_insert(task)
        if validation_pass:
            try:
                start_date, target_date = process_date_for_insert(task)
                bucket.insert(
                    [
                        {
                            "task": task_name,
                            "status": task.get("status") or states.BACKLOG,
                            "description": task.get("description"),
                            "tags": task.get("tags"),
                            "start_date": start_date,
                            "target_date": target_date,
                            "created_date": datetime.datetime.now().strftime(
                                date_format
                            ),
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


def filter_tasks_by_tags(tagstr: str, status: str = ""):
    tags = list(map(str.strip, tagstr.split(",")))
    if not status:
        tasks = bucket.find(
            lambda x: set(tags).issubset(set(x.get("tags")))
            and x.get("archived") != True
        )
    else:
        tasks = bucket.find(
            lambda x: set(tags).issubset(set(x.get("tags")))
            and x.get("status") == status
            and x.get("archived") != True
        )
    return tasks


def filter_tasks_by_status(bucket, status):
    return bucket.find(
        lambda x: x.get("status") == status and x.get("archived") != True
    )


def number_of_task_based_on_status(bucket):
    return {
        status: len(filter_tasks_by_status(bucket, status))
        for status in states.possible_states()
    }


def get_all_tasks():
    return bucket.find(lambda x: x.get("archived") != True)


def get_total_number_of_tasks(bucket):
    return len(get_all_tasks())


def get_all_tasks_ordered(reverse=True):
    all_tasks = get_all_tasks()
    return sorted(
        all_tasks,
        key=lambda i: datetime.datetime.strptime(i["created_date"], date_format),
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


def fuzzy_search(options):
    options = "\n".join(options)
    command = 'echo -n "{}" | sk'.format(options)
    selected = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE
    ).communicate()[0]
    return selected.decode("utf-8").replace("\n", "")


def display_initial_summary(total_task, tasknumber_by_status):
    console.print(
        "\n\n[bold green] total number of tasks {}[/]\n\n".format(total_task),
        justify="center",
    )
    table = Table(
        Column(states.BACKLOG, style=color_map.get(states.BACKLOG)),
        Column(states.SELECTED, style=color_map.get(states.SELECTED)),
        Column(states.RUNNING, style=color_map.get(states.RUNNING)),
        Column(states.DONE, style=color_map.get(states.DONE)),
        Column(states.REVISIT, style=color_map.get(states.REVISIT)),
        title="status summary",
        expand=True,
    )
    table.add_row(
        str(tasknumber_by_status.get(states.BACKLOG)),
        str(tasknumber_by_status.get(states.SELECTED)),
        str(tasknumber_by_status.get(states.RUNNING)),
        str(tasknumber_by_status.get(states.DONE)),
        str(tasknumber_by_status.get(states.REVISIT)),
    )
    console.print(table)
    console.print("\n\n")


def find_buckets():
    return filter(lambda x: x.suffix == ".json", task_root.iterdir())


def get_bucket_names():
    return sorted(map(lambda x: x.stem, find_buckets()))


def display_buckets():
    buckets = list(get_bucket_names())
    current_bucket = ""
    with open(current_bucket_path, "r") as current:
        current_bucket = current.read().strip() or "dump"
    try:
        current_bucket_index = buckets.index(current_bucket)
        buckets[current_bucket_index] = (
            "* [green]" + buckets[current_bucket_index] + "[/]"
        )
        console.print("\n")
        console.print("\n".join(buckets))
    except ValueError as ex:
        console.print("[red]{}".format(ex))


def display_tag_based_summary(distinct_tags):
    table = Table(
        Column("tag"),
        Column("status"),
        title="tag summary",
        expand=True,
        show_lines=True,
    )
    for tag in distinct_tags:
        content = ""
        for state in states.possible_states():
            total = len(filter_tasks_by_tags(tag, state))
            if total:
                content += "[{}] {} [/][black on grey93] {} [/] ".format(
                    color_map.get(state), state, total
                )
        table.add_row(tag, content)
    console.print(table, justify="center")


def fuzzy_search(options):
    options = "\n".join(options)
    selected = subprocess.Popen(
        fuzzy_search_command.substitute(options=options),
        shell=True,
        stdout=subprocess.PIPE,
    ).communicate()[0]
    selected = selected.decode("utf-8")
    return list(filter(None, selected.split("\n")))


@app.command()
def preview(task_name: str):
    task = bucket.find(lambda x: x.get("task") == task_name)
    display_task(task[0])


@app.command()
def new():
    filename, status = open_temp_toml_file()
    total_bookmarks = 0
    if status == 0:
        with open(filename, "r") as file:
            tasks = toml.load(file)
            insert(tasks)


@inall_app.command("find")
def inall_find(searchstr: str):
    searchstr = searchstr.strip()
    tasks = dict()
    found_tasks = dict()
    for bucket_name in get_bucket_names():
        bucket = get_bucket(bucket_name)
        tasks = bucket.find(lambda x: searchstr in x.get("task"))
        if tasks:
            found_tasks[bucket_name] = tasks
    render_in_all_table(found_tasks)


@inall_app.command("status")
def inall_status(status: str):
    status = status.strip()
    found_tasks = dict()
    for bucket_name in get_bucket_names():
        bucket = get_bucket(bucket_name)
        tasks = bucket.find(
            lambda x: x.get("status") == status and x.get("archived") != True
        )
        if tasks:
            found_tasks[bucket_name] = tasks
    render_in_all_table(found_tasks)


@tag_app.command("brief")
def tag_brief(tagstr: str, status: str = typer.Argument("")):
    tasks = filter_tasks_by_tags(tagstr, status)
    render_table(tasks)


@tag_app.command("verbose")
def tag_verbose(tagstr: str, status: str = typer.Argument("")):
    tasks = filter_tasks_by_tags(tagstr, status)
    for task in tasks:
        display_task(task)


@app.command()
def status(
    status: str = typer.Argument(states.RUNNING), display: str = typer.Argument("brief")
):
    tasks = filter_tasks_by_status(db, status)
    if tasks:
        if display == "brief":
            render_table(tasks)
        elif display == "verbose":
            for task in tasks:
                display_task(task)
        else:
            console.print("[red]display format has to be one of (brief | verbose)")


@app.command()
def edit():
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

    task_name = fuzzy_search(get_all_task_name())
    if task_name:
        task = bucket.find(lambda x: x.get("task") == task_name[0])
        if task:
            bucket.update(update, lambda x: x.get("_id") == task[0].get("_id"))


@app.command()
def editall():
    tasks = get_all_tasks_ordered()
    filename, _ = open_temp_toml_file(
        {
            str(task.get("_id")): {
                "task": task.get("task"),
                "status": task.get("status"),
                "tags": task.get("tags"),
                "description": task.get("description"),
            }
            for task in tasks
        }
    )
    new_task_details = dict()
    with open(filename, "r") as file:
        new_task_details = toml.load(file)
    for _id, edited_task in new_task_details.items():

        def update(document):
            document.update(edited_task)
            return document

        bucket.update(update, lambda y: y.get("_id") == int(_id))


@app.command()
def rm():
    def update(document):
        if document:
            document.update({"archived": True})
            console.print("[red]task id - {} is archived".format(document.get("_id")))
            return document

    task_names = fuzzy_search(get_all_task_name())
    if task_names:
        for task_name in task_names:
            task = bucket.find(lambda x: x.get("task") == task_name)
            if task:
                bucket.update(update, lambda x: x.get("_id") == task[0].get("_id"))


@app.command()
def show():
    task_name = fuzzy_search(get_all_task_name())
    if task_name:
        task = bucket.find(lambda x: x.get("task") == task_name[0])
        if task:
            display_task(task[0])


@app.command()
def summary(bucket_name: Optional[str] = typer.Argument(None)):
    if bucket_name and bucket_name not in list(get_bucket_names()) + ["all"]:
        console.print("[red]wrong bucket name passed")
    if bucket_name == "all":
        total_tasks = 0
        tasknumber_by_status = Counter({})
        for bucket_name in get_bucket_names():
            bucket = get_bucket(bucket_name)
            total_tasks += get_total_number_of_tasks(db)
            tasknumber_by_status += Counter(number_of_task_based_on_status(db))
        display_initial_summary(total_tasks, tasknumber_by_status)
    else:
        current_bucket = ""
        with open(current_bucket_path, "r") as current:
            current_bucket = current.read().strip()
        db = get_bucket(current_bucket)
        display_initial_summary(
            get_total_number_of_tasks(db), number_of_task_based_on_status(db)
        )
        distinct_tags = get_distinct_tags()
        display_tag_based_summary(distinct_tags)


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
    tasks = bucket.find(
        lambda x: searchstr in x.get("task") or searchstr in x.get("description")
    )
    for task in tasks:
        display_task(task)


@app.command()
def check(bucket: Optional[str] = typer.Argument(None)):
    if not bucket:
        display_buckets()
    else:
        bucket = bucket.strip()
        with open(current_bucket_path, "w") as current:
            current.write(bucket)


@app.command()
def reindex():
    bucket.index._id = 0

    def update(document):
        document.update({"_id": bucket.index._id})
        return document

    tasks = get_all_tasks_ordered(reverse=False)
    for task in tasks:
        bucket.index.increment()
        bucket.update(update, lambda x: x.get("_id") == task.get("_id"))
    console.print("[green]re-indexing done for {} tasks!".format(len(tasks)))


def get_bucket(bucket_name):
    return jsondb(str(pathlib.Path(task_root / "{}.json".format(bucket_name))))


def init_db():
    if not current_bucket_path.exists():
        current_bucket_path.touch()
    with open(current_bucket_path, "r") as current:
        current_bucket = current.read().strip() or "dump"
        db = jsondb(str(pathlib.Path(task_root / "{}.json".format(current_bucket))))
        db.set_index("task")
        db.set_index("_id")
        return db


bucket = init_db()
if __name__ == "__main__":
    if not shutil.which("sk"):
        console.print("[bold red]could not find sk in path")
        console.print("install from https://github.com/lotabout/skim")
    else:
        app()
