import subprocess
import sys
import os
import toml
import shutil
from rich.console import Console

console = Console()

def are_all_commands_valid(config):
    flag = True
    for item in config.values():
        command = item.get('dependent')
        if not shutil.which(command):
            flag = False 
            console.log('command not in PATH or Installed {}'.format(command))
    return flag

    
def execute_commands(commands):
    with console.status('[bold green]Installing packages...') as status:
        for command in commands:
            subprocess.run(
                command,
                stdout=open('/tmp/postinstall_stdout.log', 'a'),
                stderr=open('/tmp/postinstall_stderr.log', 'a')
            ) 
            console.log(f' complete')


def parse_config(path):
    try:
        config = toml.load(path)
    except:
        console.log('[red][TomlDecodeError] Unable to parse config')

    return config

def parse_args(args):
    if len(args) > 2:
        sys.exit('not enough arguments provided')

    if args[1] == '--path':
        path = args[2]
        if path and os.path.exists(path):
            return path
        else:
            console.log('config path invalid or not provided')
    else:
        console.log('path args not provided')
    return None

def run():
    path = parse_args(sys.argv)
    config = parse_config(path)
    if are_all_commands_valid(config):
        execute_commands()
    else:
        pass #wrong config path

if __name__ == "__main__":
    run()
