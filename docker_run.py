'''
Functions specific to Docker RUN
'''
import re
import yaml

# package management tools
pm_tools_file = 'package_management.yml'
pm_tools = {}
with open(pm_tools_file) as f:
    pm_tools = yaml.safe_load(f)


def get_shell_commands(run_comm):
    '''Given a RUN command return a list of shell commands to be run'''
    comm_list = run_comm.split('&&')
    cleaned_list = []
    for comm in comm_list:
        cleaned_list.append(comm.strip())
    return cleaned_list


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
