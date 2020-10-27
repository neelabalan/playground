import subprocess
import logging
import argparse
import os
try:
    import toml
    from yaspin import yaspin
except ImportError as error:
    print("module not found - {}".format(error))


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# creating file handler
logpath = os.path.join(os.getenv('HOME'), 'postinstall.log')
handler = logging.FileHandler(logpath)
handler.setLevel(logging.INFO)

# creating logging format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%d-%m-%Y--%H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

def getPrefix(config):
    ''' returns the dict of containers to install '''
    return config.get('repo').get('prefix')

def getCommands(programs, prefix):
    if type(programs) is list:
        listOfCommandString = list(
            map(
                lambda program: prefix + ' ' + program, programs 
            )
        )
        return tuple(
            map(
                lambda command: command.split(' '), listOfCommandString
            )
        )
    else:
        command = prefix + ' ' + programs 
        return (list(command.split(' ')), )

def executeCommands(commands):
    stdoutpath = os.path.join(os.getenv('HOME'), 'stdout.log')
    stderrpath = os.path.join(os.getenv('HOME'), 'stderr.log')
    stdoutlog = open(stdoutpath, 'a')
    stderrlog = open(stderrpath, 'a')

    logger.info('comands - {}'.format(commands))
    for command in commands:
        logger.info('executing command {}'.format(command))
        subprocess.run(
            command,
            stdout=stdoutlog, 
            stderr=stderrlog
        ) 


def installPackages(config):
    ''' install required package from selected containers '''
    programsToBeInstalled = getPrefix(config)
    logger.info('programs to be installed - {}'.format(programsToBeInstalled))
    for selected, prefix in programsToBeInstalled.items():
        # executing sample sudo command
        subprocess.run(['sudo', 'ls'], stdout=subprocess.DEVNULL)
        # new line
        print('\n') 
        print('installting packages from {}'.format(selected.upper()))
        repo = config.get('repo').get(selected)
        for package, programs in repo.items():
            with yaspin(text = "installing {} packages".format(package), color='blue') as spinner:
                try:
                    commands = getCommands(programs, prefix)
                    executeCommands(commands) 
                    logger.info('installed - {}'.format(programs))
                    spinner.color= 'green'
                    spinner.ok('SUCCESS')
                except:
                    logger.info('falied to install - {}'.format(programs))
                    spinner.color = 'red'
                    spinner.fail('FAILED')

def areValidPaths(paths):
    return all([os.path.exists(path) for path in paths])

def deployDotfiles(config):
    ''' deploy dotfiles '''
    dconf     = config.get('dotfile')
    sourcedir = dconf.get('source')
    targetdir = dconf.get('target')
    files     = dconf.get('files')

    required = (sourcedir, targetdir, files)
    precheck = all(required) and areValidPaths([sourcedir]) and areValidPaths([targetdir]) and areValidPaths(files)
    if precheck:
        if type(files) == list:
            print('deploying dotfiles...')
            for file in files:
                command = 'ln -sf '+ sourcedir + ' ' + targetdir
                print('-> {}', file)
                subprocess.run(command)
        else:
            print('files in config.toml needs to be in list format')
    else:
        print('one or more config/file missing for dotfile deployment')


def main():
    configpath = os.getenv('HOME') + '/config.toml'
    with open(configpath) as config:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-i', 
            '--install',
            action  = 'store_true',
            help    = 'installs the packages set in config.toml in home directory'
        )
        parser.add_argument(
            '-d', 
            '--deploy',   
            action  = 'store_true',
            help    = 'deploys dotfiles from .dotfile directory containing dotfiles (expected to be in home directory)'
        )
        args = parser.parse_args()
        configdict = toml.load(config)
        if not args.install:
            logger.info('proceeding to install packages')
            installPackages(configdict) 
        if args.deploy:
            logger.info('proceeding to deploy dotfiles')
            deployDotfiles(configdict)
        if not args.install and not args.deploy:
            print('''No arguments provded
                -i / --install to install packages provided in config.toml
                -d / --deploy to deploy dotfiles to HOME directory'''
            )

if __name__ == "__main__":
    main()
