import subprocess
import toml
from yaspin import yaspin
import colorama 
import os
import argparse

# lambdas
colorama.init()
# do lambdas slow the program?
bstring = lambda string: '\033[94m' + string + '\033[0m'
ystring = lambda string: '\033[93m' + string + '\033[0m'
# rprint = lambda string: print('\033[91m' + string + '\033[0m')
# gprint = lambda string: print('\033[92m' + string + '\033[0m')



def getContainersToInstall(containers):
	''' returns the dict of containers to install '''
	return containers.get('container').get('toInstall')

def installPackages(containers, containersToInstall):
	''' install required package from selected containers '''
	for selected, prefix in containersToInstall.items():
		print(bstring('installting packages from {}'.format(selected)))
		container = containers.get('container').get(selected)
		subprocess.run(['sudo', 'ls'], stdout=subprocess.DEVNULL)
		for box, packages in container.items():
			with yaspin(text = "installing {} packages".format(box), color='blue') as spinner:
				try:
					commands = getCommands(packages, prefix)
					executeCommands(commands) #something
					spinner.color= 'green'
					spinner.ok('SUCCESS')
				except:
					spinner.color = 'red'
					spinner.fail('FAILED')
					

def getCommands(packages, prefix):
	if type(packages) is list:
		listOfCommandString = list(
			map(
				lambda package: prefix + ' ' + package, packages
			)
		)
		return tuple(
			map(
				lambda command: command.split(' '), listOfCommandString
			)
		)
	else:
		command = prefix + ' ' + packages
		return (list(command.split(' ')), )

def executeCommands(commands):
	for command in commands:
		subprocess.run(
			command,
			stdout=subprocess.DEVNULL, 
			stderr=subprocess.DEVNULL
		) 

if __name__ == "__main__":
	with open('package.toml') as package:
		# validate the args.install - using try and except
		containers = toml.load(package)
		installPackages(containers, getContainersToInstall(containers))
	'''
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'-i', 
		'--install',
		action  = 'store_true',
		help    = 'installs the packages based on package.toml config in current directory'
	)
	parser.add_argument(
		'-d', 
		'--deploy',   
		action  = 'store_true',
		help    = 'deploys dotfiles and configs based on config.toml in current directory'
	)
	parser.add_argument('-u', '--update',   help='update the configuration using git pull or git push')
	args = parser.parse_args()

	if args.install:
		
			# print('install argument is now provided {}'.format(args.install))
	# if args.deploy:
	# 	with open('config.toml') as config:
	# 		cConfig = toml.load(config)
	# 		print('config argument in place')
	# if args.update:
	# 	pass
	'''



