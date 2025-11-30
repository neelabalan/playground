import os
import shutil
import subprocess
import sys

import toml
from rich.console import Console

console = Console()


def are_all_commands_valid(config):
    """
    args (dict) - config
    returns (bool, list)
        - True if atleast one command is found in PATH
        - the commands not found in PATH
    """
    commands_not_found = list()
    for item in config.values():
        command = item.get('dependent')
        if not shutil.which(command):
            commands_not_found.append(command)

    return len(config.values()) == commands_not_found, commands_not_found


def get_commands(package_info):
    base_command = package_info.get('command')
    return map(lambda x: ' '.join([base_command, x]), package_info.get('packages'))


def execute_commands(config):
    """
    args (dict) - config
    returns (None)
    """
    for item in config:
        commands = get_commands(config[item])
        with console.status('[bold green]Installing {} packages...'.format()) as status:
            for command in commands:
                subprocess.run(
                    command,
                    stdout=open('/tmp/postinstall_stdout.log', 'a'),
                    stderr=open('/tmp/postinstall_stderr.log', 'a'),
                )
                console.log(f' complete')


def parse_config(path):
    """
    args (str) - path
    return (dict) - config
    """
    try:
        config = toml.load(path)
    except:
        console.print('[red]TomlDecodeError - Unable to parse config')

    return config


def parse_args(args):
    if len(args) > 2:
        sys.exit('not enough arguments provided')

    if args[1] == '--path':
        path = args[2]
        if path and os.path.exists(path):
            return path
        else:
            console.print('config path provided is either invalid or not provided')
    else:
        console.print('--path args not provided')
    return None


def run():
    path = parse_args(sys.argv)
    config = parse_config(path)
    proceed_further, invalid_commands = are_all_commands_valid(config)
    if proceed_further:
        console.print('The commands {} are not found in PATH or not installed'.format(str(invalid_commands)))
        if proceed_further:
            console.print('Would like to proceed further with the installation (y/n) ')
            choice = input()
            if choice == 'y':
                execute_commands(config)
            else:
                sys.exit('exiting program')
    else:
        console.print('All of the given commands are not found in PATH or is not installed')


if __name__ == '__main__':
    run()
