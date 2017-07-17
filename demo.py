'''
Docker compliance tool demo
This is a basic imlementation of what the compliance tool is supposed
to accomplish at the basic level

Objective:
    Given a Dockerfile used to build a Docker image, produce a tarball
    of all the sources for the binaries installed in the image along with
    a report containing all of the installed binaries

Steps:
    1. Read the dockerfile and get all the package management tools
    used and a list of packages that were installed
    2. Build the docker image and run a container
    3. Use the package management tools to download the sources
    4. Copy the sources out along with a report containing the list of
    packages
    5. Stop the container, delete the image and exit
'''

import argparse
import os
import re
import subprocess
from contextlib import contextmanager

import dockerfile as d
import docker_from as df
import docker_run as dr

# docker commands
build = ['docker', 'build']
run = ['docker', 'run', '-td']
copy = ['docker', 'cp']
execute = ['docker', 'exec']
stop = ['docker', 'stop']
remove = ['docker', 'rm']
delete = ['docker', 'rmi']

# docker container names
image = 'doctective'
container = 'doc-working'


# from https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextmanager
def pushd(path):
    curr_path = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(curr_path)


def docker_command(command, sudo=True, *extra):
    '''Invoke docker command'''
    full_cmd = []
    # check if sudo
    # TODO: need some way of checking if the user is added to the
    # docker group so they already have privileges
    if sudo:
        full_cmd.append('sudo')
    full_cmd.extend(command)
    for arg in extra:
        full_cmd.append(arg)
    # invoke
    try:
        print("Running command: " + ' '.join(full_cmd))
        subprocess.check_call(full_cmd)
    except subprocess.CalledProcessError as error:
        print("Error calling: " + error.cmd)


def get_packages(docker_commands, package_type):
    '''Given the docker commands in a dockerfile,  get a dictionary of
    package management tools and the packages installed with it
    The package type is either an installed package or a downloaded
    package
    For a downloaded package we cannot determine if they are source
    or binaries so we assume the packages are manually installed and
    cannot be traced back to sources'''
    pm_dict = {}
    shell_commands = []
    for docker_command in docker_commands:
        if docker_command[0] == 'RUN':
            shell_commands.extend(dr.get_shell_commands(docker_command[1]))
    for command in shell_commands:
        command_obj = dr.parse_command(command)
        if command_obj['name'] in dr.pm_tools[package_type].keys():
            if command_obj['name'] in pm_dict.keys():
                pm_dict[command_obj['name']].extend(command_obj['arguments'])
            else:
                pm_dict.update({command_obj['name']: command_obj['arguments']})
    return pm_dict


def get_tag_name(docker_commands):
    '''The image tag for the running container is the name of the original
    image in the Dockerfile
    NOTE: investigate generating this'''
    # Assuming all Dockerfiles start with a FROM
    return df.parse_image_tag(docker_commands[0][1])[0]


def start_container(dockerfile, image_tag_string):
    '''Invoke docker command to build a given docker image and start it
    Assumptions: Docker is installed and the docker daemon is running
    There is no other running container from the given image'''
    # TODO: there may be an existing image one would want to build in
    # which case move the build part out into a different module
    path = os.path.dirname(dockerfile)
    with pushd(path):
        docker_command(build, True, '-t', image_tag_string, '-f',
                       os.path.basename(dockerfile), '.')
    docker_command(run, True, '--name', container, image_tag_string)


def extract_sources(binaries, base_tag_string, image_tag_string):
    '''Given a dictionary containing the package management tool and the
    list of installed packages, extract out a tarball of the sources
    '''
    # Assuming that there is now a running container
    # For each package management tool in binaries see if there are any
    # config files that need to be copied over and any commands to invoke
    image_tag = df.parse_image_tag(base_tag_string)
    for pmt in binaries.keys():
        if 'copy' in dr.pm_tools['assisted'][pmt].keys():
            for cp_action in dr.pm_tools['assisted'][pmt]['copy']:
                from_str = re.sub('image', image_tag[0], cp_action['from'])
                from_str = re.sub('tag', image_tag[1], from_str)
                from_str = from_str + cp_action['file']
                to_str = cp_action['to'] + cp_action['file']
                try:
                    docker_command(copy, True, from_str,
                                   container + ':' + to_str)
                except:
                    print("Error in copying files into container!")
                    print("Cleaning up...")
                    cleanup(image_tag_string)
        if 'invoke' in dr.pm_tools['assisted'][pmt].keys():
            count = len(dr.pm_tools['assisted'][pmt]['invoke'].keys()) + 1
            for step in range(1, count):
                cmd_obj = dr.pm_tools['assisted'][pmt]['invoke'][step]
                if cmd_obj['args'] == '*':
                    args = ' '.join(binaries[pmt])
                else:
                    args = ''
                full_cmd = cmd_obj['command'] + ' ' + args
                try:
                    docker_command(
                        execute, True, container, '/bin/bash', '-c', full_cmd)
                except:
                    print("Error in executing command inside the container")
                    print("Cleaning up....")
                    cleanup(image_tag_string)
        if 'retrieve' in dr.pm_tools['assisted'][pmt].keys():
            from_str = container + ":" + dr.pm_tools[
                'assisted'][pmt]['retrieve']['from']
            to_str = dr.pm_tools['assisted'][pmt]['retrieve']['to']
            try:
                docker_command(copy, True, from_str, to_str)
            except:
                print("Error in copying files outside the container")
                print("Cleaning up....")
                cleanup(image_tag_string)


def cleanup(image_tag_string):
    '''Clean up running container'''
    # stop container
    docker_command(stop, True, container)
    # remove the container
    docker_command(remove, True, container)
    # delete the image
    docker_command(delete, True, image_tag_string)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dockerfile')
    args = parser.parse_args()
    docker_commands = d.get_directive_list(d.get_command_list(args.dockerfile))
    base_image_tag = docker_commands[0][1]
    installed_binaries = get_packages(docker_commands, 'assisted')
    downloaded_packages = get_packages(docker_commands, 'manual')
    image_tag_string = image + ':' + get_tag_name(docker_commands)
    start_container(args.dockerfile, image_tag_string)
    if not os.path.exists('sources'):
        os.makedirs('sources')
    extract_sources(installed_binaries, base_image_tag, image_tag_string)
    cleanup(image_tag_string)
