import subprocess
import json
list_command = 'az group list'
delete_command = 'az group delete --yes --name {}'
def run():
    response = subprocess.Popen(list_command.split(' '), stdout=subprocess.PIPE)
    output, _ = response.communicate()
    resources = json.loads(output)
    for resource in resources:
        resource_name =  resource.get('name')
        subprocess.run(delete_command.format(resource_name).split(' '))

if __name__ == '__main__':
    run()

