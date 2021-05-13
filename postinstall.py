import subprocess
import logging
import os
import toml
import shutil
from rich.console import Console

console = Console()
# tasks = [f"task {n}" for n in range(1, 11)]

# with console.status("[bold green]Working on tasks...") as status:
#     while tasks:
#         task = tasks.pop(0)
#         sleep(1)
#         console.log(f"{task} complete")

def get_commands(config):
    ''' returns the dict of containers to install '''
    return config.get('repo').get('commands')


def are_all_commands_valid(config):
    flag = True
    for item in config.values():
        command = item.get('dependent')
        if not shutil.which(command):
            flag = False 
            console.log('command not in PATH or Installed {}'.format(command))
    return flag

    
def execute_commands(commands):
    for command in commands:
        subprocess.run(
            command,
            stdout=open('/tmp/postinstall_stdout.log', 'a'),
            stderr=open('/tmp/postinstall_stderr.log', 'a')
        ) 


def run():
    pass


if __name__ == "__main__":
    run()
