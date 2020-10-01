import subprocess
import toml
from yaspin import yaspin
import colorama 
import os
import argparse

colorama.init()
bstring = lambda string: '\033[94m' + string + '\033[0m'
ystring = lambda string: '\033[93m' + string + '\033[0m'
# rprint = lambda string: print('\033[91m' + string + '\033[0m')
# gprint = lambda string: print('\033[92m' + string + '\033[0m')


def getPrefix(config):
	''' returns the dict of containers to install '''
	return config.get('repo').get('prefix')

def getCommands(programs, prefix):
	if type(programs) is list:
		listOfCommandString = list(
			map(
				lambda program: prefix + ' ' + programs, programs 
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
	for command in commands:
		subprocess.run(
			command,
			stdout=subprocess.DEVNULL, 
			stderr=subprocess.DEVNULL
		) 


def installPackages(config):
	''' install required package from selected containers '''
	programsToBeInstalled = getPrefix(config)
	for selected, prefix in programsToBeInstalled.items():
		print(bstring('installting packages from {}'.format(selected)))
		repo = config.get('repo').get(selected)
		# executing sample sudo command
		subprocess.run(['sudo', 'ls'], stdout=subprocess.DEVNULL)

		for package, programs in repo.items():
			with yaspin(text = "installing {} packages".format(package), color='blue') as spinner:
				try:
					commands = getCommands(programs, prefix)
					executeCommands(commands) 
					spinner.color= 'green'
					spinner.ok('SUCCESS')
				except:
					spinner.color = 'red'
					spinner.fail('FAILED')
					

if __name__ == "__main__":
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
		if args.install:
			installPackages(configdict) 