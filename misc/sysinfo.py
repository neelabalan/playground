import subprocess
import os


list_of_commands = [
    "baseboard",
    "bios",
    "cdrom",
    "computersystem",
    "cpu",
    "diskdrive",
    "dcomapp",
    "environment",
    "memlogical",
    "memphysical",
    "nic",
    "os",
    "printer",
    "process",
    "product",
    "qfe",
    "sounddev",
    "startup",
    "sysaccount",
    "sysdriver",
    "timezone",
    "useraccount"
]

root_path = 'system-info\\'

def format_command( command ):
    return "wmic " + command + " list full /format:hform"

def mkdir_if_not_exists( path ):
    if not os.path.exists( path ):
        os.makedirs( path ) 

def store_sysinfo():
    for command in list_of_commands:
        filepath = root_path + command + '.html'
        with open( filepath, 'w' ) as file:
            try:
                process = subprocess.Popen( format_command( command ).split( ' ' ), stdout = file)
            except:
                print('EXCEPTION command not executable {}'.format( command ))

if __name__ == "__main__":
    mkdir_if_not_exists( root_path )
    store_sysinfo()