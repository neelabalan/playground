import base64
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

import pyskim
import toml
import typer
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from jsondb import jsondb
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

app = typer.Typer()
app_locked = typer.Typer()
db = None

date_format = '%a %d %b %Y %X'
SEPERATOR = '+++'


class RichStyles:
    title = Style(color='green', bold=True)
    tag = Style(color='black', bgcolor='blue')


class Paths:
    note_root = pathlib.Path.home() / '.local/qn/'
    note_path = pathlib.Path.home() / '.local/qn/qn.json'
    enc_path = pathlib.Path.home() / '.local/qn/qn.enc'


def open_temp_md_file(
    template={
        'title': '',
        'tags': [],
        'created_date': datetime.datetime.now().strftime(date_format),
    },
    mdtext='',
):
    fd, filename = tempfile.mkstemp(suffix='.md', text=True)
    with open(filename, 'w') as file:
        file.write(SEPERATOR + '\n' + toml.dumps(template) + SEPERATOR + mdtext)
    write_status = subprocess.call('$EDITOR {}'.format(filename), shell=True)
    return filename, write_status


def parse_front_matter(filepath):
    filestr = ''
    with open(filepath, 'r') as file:
        filestr = file.read()
    if filestr:
        strlist = filestr.split(SEPERATOR)
        if strlist and strlist[1]:
            try:
                fmdict = toml.loads(strlist[1])
                return fmdict
            except toml.TomlDecodeError as err:
                print('error encountered while decoding TOML string - {}'.format(str(filepath)))


def distinct_tags():
    tags = list()
    notes = db.find(lambda x: True)
    for note in notes:
        tags.extend(note.get('tags'))
    return sorted(list(set(tags)))


def distinct_titles():
    notes = db.find(lambda x: True)
    return [note.get('title') for note in notes]


def extract_md_text(filepath):
    filestr = ''
    with open(filepath, 'r') as file:
        filestr = file.read()
    if filestr:
        strlist = filestr.split(SEPERATOR)
        if strlist and strlist[2]:
            return strlist[2]


def display_note(note):
    console = Console(color_system='256')
    tags = Text()
    for tag in note.get('tags'):
        tags.append('#{}'.format(tag), style=RichStyles.tag)
        tags.append(' ─ ')

    console.print(
        Panel(
            Markdown(note.get('note') or '>', code_theme='ansi_dark'),
            title=note.get('title'),
            title_align='center',
            subtitle=tags + Text(note.get('created_date')),
            subtitle_align='right',
        )
    )
    print('\n')


def filter_notes_by_tags(tags):
    return db.find(lambda x: set(tags).issubset(set(x.get('tags'))))


def get_all_notes_ordered(reverse=True):
    all_notes = db.find(lambda x: True)
    return sorted(
        all_notes,
        key=lambda i: datetime.datetime.strptime(i['created_date'], date_format),
        reverse=reverse,
    )


@app.command()
def preview(title: str):
    note = db.find(lambda x: x.get('title') == title)
    display_note(note[0])


@app.command()
def tag():
    tags = pyskim.skim(
        distinct_tags(),
        '-m --ansi --bind="ctrl-a:select-all"',
    )
    if tags:
        notes = db.find(lambda x: set(tags).issubset(set(x.get('tags'))))
        titles = [note['title'] for note in notes]
        title = pyskim.skim(
            titles,
            '--color="prompt:27,pointer:27" --preview="qn preview {}" --preview-window=up:50%',
        )
        if title:
            note = db.find(lambda x: x.get('title') == title[0])
            display_note(note[0])


@app.command()
def view():
    title = fuzzy_search(distinct_titles())
    if title:
        note = db.find(lambda x: x.get('title') == title[0])
        if note:
            display_note(note)


@app.command()
def find(searchstr: str):
    searchstr = searchstr.strip()
    notes = db.find(lambda x: searchstr in x.get('title') or searchstr in x.get('note'))
    display_notes(notes)


@app.command()
def rm():
    title = pyskim.skim(
        distinct_titles(),
        '--ansi --preview="qn preview {}" --preview-window=up:50% --bind="ctrl-a:select-all"',
    )
    if title:
        deleted_doc = db.delete(lambda x: x.get('title') == title[0])
        if deleted_doc:
            print('[red]note "{}" deleted'.format(title[0]))


@app.command()
def encrypt(password: str = typer.Option(..., prompt=True, confirmation_prompt=True, hide_input=True)):
    cipher_text = ''
    hasher = hashlib.sha3_256()
    hasher.update(password.encode('utf-8'))
    fernet = Fernet(base64.urlsafe_b64encode(hasher.digest()))
    with open(Paths.note_path, 'r') as file:
        cipher_text = fernet.encrypt(file.read().encode('utf-8'))
    Paths.note_path.unlink()
    with open(Paths.enc_path, 'w') as file:
        file.write(cipher_text.decode('utf-8'))


@app_locked.command()
def decrypt(password: str = typer.Option(..., prompt=True, hide_input=True)):
    cipher_text = plain_text = ''
    hasher = hashlib.sha3_256()
    hasher.update(password.encode('utf-8'))
    fernet = Fernet(base64.urlsafe_b64encode(hasher.digest()))
    with open(Paths.enc_path, 'r') as file:
        cipher_text = file.read()
    try:
        plain_text = fernet.decrypt(cipher_text.encode('utf-8'))
        with open(Paths.note_path, 'w') as file:
            file.write(plain_text.decode('utf-8'))
        Paths.enc_path.unlink()
    except InvalidToken as e:
        print('[red]invalid password')


@app.command()
@app_locked.command()
def export(path: str):
    pass


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    def update(document):
        if document:
            filename, status = open_temp_md_file(
                {
                    'title': note['title'],
                    'tags': note['tags'],
                    'created_date': note['created_date'],
                },
                mdtext=note['note'],
            )
            with open(filename, 'r') as file:
                updated_front_matter = parse_front_matter(filename)
                updated_text = extract_md_text(filename)
                document.update(**updated_front_matter, **{'note': updated_text})
                return document

    if not ctx.invoked_subcommand:
        title = pyskim.skim(
            distinct_titles(),
            '--ansi --print-query --print-cmd --preview="qn preview {}" --preview-window=up:50% --bind="ctrl-a:select-all"',
        )
        if title:
            title = title[-1]
            note = db.find(lambda x: x.get('title') == title)
            if note:
                note = note[0]
                db.update(update, lambda x: x.get('title') == title)
            else:
                filename, status = open_temp_md_file(
                    {
                        'title': title,
                        'tags': [],
                        'created_date': datetime.datetime.now().strftime(date_format),
                    }
                )
                front_matter = parse_front_matter(filename)
                front_matter['title'] = front_matter['title'] or title
                db.insert(
                    [
                        {
                            **parse_front_matter(filename),
                            **{'note': extract_md_text(filename)},
                        }
                    ]
                )
                print('[green]new note added')


def run():
    if not Paths.enc_path.exists():
        global db
        db = jsondb(str(Paths.note_path))
        db.set_index('title')
        app()
    else:
        app_locked()
    Paths.note_root.mkdir(parents=True, exist_ok=True)
