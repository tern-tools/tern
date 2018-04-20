'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''
import os
import re

from contextlib import contextmanager


# from https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextmanager
def pushd(path):
    curr_path = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(curr_path)


def parse_command(command):
    '''Parse a unix command of the form:
        command (subcommand) [options] [arguments]
        Caveats:
            1. There is no way of knowing whether a command contains
            subcommands or not so those tokens will be identified as 'words'
            2. There is no way of knowing whether an option requires an
            argument or not. The arguments will be identified as 'words'
        For most cases involving package management this should be enough to
        identify whether a package was meant to be installed or removed.
    Convert a given command into a dictionary of the form:
        {'name': command,
         'options': [list of option tuples]
         'words': [remaining words]}
    An option tuple contains the option flag and the option argument
    We look ahead to see if the token after the option flag does not match
    the regex for an option flag and assumes that is the argument
    The token still remains in the words list because we do not know for sure
    if it is a command argument or an option argument'''
    options = re.compile('^-')
    option_list = []
    word_list = []
    command_dict = {}
    command_tokens = command.split(' ')
    # first token is the command name
    command_dict.update({'name': command_tokens.pop(0)})
    # find options in the rest of the list
    while command_tokens:
        if options.match(command_tokens[0]):
            option_flag = command_tokens.pop(0)
            if not options.match(command_tokens[0]):
                option_arg = command_tokens[0]
            else:
                option_arg = ''
            option_list.append((option_flag, option_arg))
        else:
            word_list.append(command_tokens.pop(0))
    # now we have options and the remainder words
    command_dict.update({'options': option_list,
                         'words': word_list})
    return command_dict
