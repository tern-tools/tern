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
image = 'doctective'
container = 'doc-working'


# sources library
cmd_lib_file = 'command_library.yml'
command_lib = {}
with open(cmd_lib_file) as f:
    command_lib = yaml.safe_load(f)


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
