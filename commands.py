import os
import re
import subprocess
import yaml

from contextlib import contextmanager

'''
Shell and docker command parser, information retrieval and invoking
'''
# docker commands
build = ['docker', 'build']
run = ['docker', 'run', '-td']
copy = ['docker', 'cp']
execute = ['docker', 'exec']
stop = ['docker', 'stop']
remove = ['docker', 'rm']
delete = ['docker', 'rmi']

# docker container names
# TODO: randomly generated image and container names
image = 'doctective'
container = 'doc-working'


# sources library
cmd_lib_file = 'command_library.yml'
command_lib = {}
with open(cmd_lib_file) as f:
    command_lib = yaml.safe_load(f)

# package rules
all_pkgs = '*'
one_pkg = ''
# TODO: check if reporting source urls for package management systems is OK
not_appl = 'NA'


def get_shell_commands(run_comm):
    '''Given a RUN command return a list of shell commands to be run'''
    comm_list = run_comm.split('&&')
    cleaned_list = []
    for comm in comm_list:
        cleaned_list.append(comm.strip())
    return cleaned_list


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
    result = ''
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
        result = subprocess.check_output(full_cmd)
    except subprocess.CalledProcessError as error:
        print("Error calling: " + error.cmd)
    return result


def parse_command(command):
    '''Typically a unix command is of the form:
        command (subcommand) [options] [arguments]
    Convert a given command into a dictionary of the form:
        {'name': command,
         'subcommand': subcommand,
         'options': [list of options]
         'arguments': [list of arguments]}'''
    options = re.compile('^-')
    options_list = []
    args_list = []
    command_dict = {}
    command_words = command.split(' ')
    # first word is the command name
    command_dict.update({'name': command_words.pop(0), 'subcommand': ''})
    # check if the first word is an option
    first = command_words.pop(0)
    if not options.match(first):
        # this is a subcommand
        command_dict.update({'subcommand': first})
    else:
        # append this to the list of options
        options_list.append(first)
    # find options and arguments in the rest of the list
    while command_words:
        if options.match(command_words[0]):
            options_list.append(command_words.pop(0))
        else:
            args_list.append(command_words.pop(0))
    # now we have options and arguments
    command_dict.update({'options': options_list,
                         'arguments': args_list})
    return command_dict


def check_sourcable(package_name):
    '''Given a package name find out if the sources can be traced back.
    We find this out by checking the package against the command library
    If the package has a url or source retrieval steps associated with it
    then we return True. If not then we return false'''
    sourcable = False
    for command in command_lib.keys():
        for package in command_lib[command]['packages']:
            # check if one of these are defined in the library
            if 'url' in package.keys() or \
                    'url_retrieval' in package.keys() or \
                    'src_retrieval' in package.keys():
                sourcable = True
    return sourcable


def get_packages(docker_commands):
    '''Given the docker commands in a dockerfile,  get a dictionary of
    packages that are in the command library of retrievable sources
    If it does not exist in the library then record them under
    unrecognized packages'''
    pkg_dict = {}
    pkg_dict.update({'recognized': {}, 'unrecognized': {}})
    shell_commands = []
    for docker_command in docker_commands:
        if docker_command[0] == 'RUN':
            shell_commands.extend(get_shell_commands(docker_command[1]))
    for command in shell_commands:
        command_obj = parse_command(command)
        if command_obj['name'] in command_lib.keys():
            if check_sourcable(command_obj['name']):
                if command_obj['name'] in pkg_dict['recognized'].keys():
                    pkg_dict['recognized'][command_obj['name']].extend(
                        command_obj['arguments'])
                else:
                    pkg_dict['recognized'].update(
                        {command_obj['name']: command_obj['arguments']})
            else:
                if command_obj['name'] in pkg_dict['unrecognized'].keys():
                    pkg_dict['unrecognized'][command_obj['name']].extend(
                        command_obj['arguments'])
                else:
                    pkg_dict['unrecognized'].update(
                        {command_obj['name']: command_obj['arguments']})
    return pkg_dict


def remove_uninstalled(pkg_dict):
    '''Given a dictionary of commands and the packages that got installed
    with it, remove the ones that got uninstalled.
    Currently, there is a happy coincidence that if a package was installed
    and then uninstalled, they occur as duplicates in the list of packages.
    This may not always be true though so this should be something to test'''
    for command in pkg_dict.keys():
        pkg_list = pkg_dict[command]
        remain_list = []
        while pkg_list:
            pkg = pkg_list.pop()
            if pkg in remain_list:
                remain_list.remove(pkg)
            else:
                remain_list.append(pkg)
        pkg_dict[command] = remain_list
    return pkg_dict


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


def cleanup(image_tag_string):
    '''Clean up running container'''
    # stop container
    docker_command(stop, True, container)
    # remove the container
    docker_command(remove, True, container)
    # delete the image
    docker_command(delete, True, image_tag_string)


def invoke_in_container(invoke_dict, package):
    '''Invoke the commands from the invoke dictionary within a running
    container. The invoke dictionary looks like:
        <step>:
            command: <the command to invoke>
            args: <True/False>
    update this dict with the result from each command invoked'''
    count = invoke_dict.keys()
    for step in range(1, count):
        full_cmd = ''
        command = invoke_dict[step]['command']
        # check if there are any arg rules
        if 'args' in invoke_dict[step].keys():
            if invoke_dict[step]['args']:
                full_cmd = command + ' ' + package
            else:
                full_cmd = command
            try:
                result = docker_command(execute, True, container, '/bin/bash',
                                        '-c', full_cmd)
                invoke_dict[step].update({'result': result})
            except:
                print("Error executing command inside the container")
                break
        else:
            print("Please specify if the package name should be an argument"
                  " for this command")
            break
    return invoke_dict
