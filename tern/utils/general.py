# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import os
import random
import re
import regex
import tarfile
import shlex
import subprocess  # nosec
from contextlib import contextmanager
from pathlib import Path
from pbr.version import VersionInfo

from tern.utils import constants


# regex strings
cleaning = '[\t\\\\]'
concat = '&&|;'


# from https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextmanager
def pushd(path):
    curr_path = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(curr_path)


def get_top_dir(working_dir=None):
    '''Get the hidden working directory'''
    if working_dir:
        return os.path.join(working_dir, constants.dot_folder)
    return os.path.join(str(Path.home()), constants.dot_folder)


def initialize_names():
    randint = random.randint(10000, 99999)  # nosec
    constants.image = constants.image + "_" + str(randint)
    constants.tag = constants.tag + "_" + str(randint)
    constants.container = constants.container + "_" + str(randint)


def clean_command(command):
    '''Given a command string (only contains one command, does not contain &&
    or ;), clean out all whitespaces, tabs and line indentations'''
    return ' '.join(shlex.split(command)).replace('\n', '')


def split_command(shell_script):
    """Given a shell script, split it into statements:
    - command: a single line command which may install softwares.
    - variable: variable assignment in the shell script.
    - loop: a block of code which iters(for while until). We will extract
        the commands in the loop.
    - branch: a block of code contains branches(case if). We will NOT
        extract info in this since we are not sure which branch will
        be executed.
    """
    # pattern for skipping single and double quote
    skip_pattern = r"\".*?\"(*SKIP)(*F)|'.*?'(*SKIP)(*F)"
    # pattern for split a concatenated command
    match_pattern = r':;|&&|;|\|\|'
    pattern = skip_pattern + '|' + match_pattern
    concatenated_commands = regex.split(pattern, shell_script)
    # use keywords to match loop, branch.
    keywords = {'for': 'done', 'if': 'fi', 'case': 'esac', 'while': 'done'}
    start_keywords = tuple(keywords.keys())
    # current_keyword[0] is start_keyword, eg. 'for'.
    # current_keyword[1] is end_keyword, eg. 'done'.
    current_keyword = ("", "")
    # store loop and branch commands
    commands_string = []
    statements = []
    for cmd in concatenated_commands:
        # remove '{}' '()'
        cmd = cmd.strip(" \t{}()")
        # skip empty `cmd`
        if not cmd:
            continue
        # `commands_string` is empty means we are not in a loop or branch,
        # so we need to check keywords first.
        if not commands_string:
            # quick check on keywords
            if cmd.startswith(start_keywords):
                # if match, go throgh keywords to find which one is matched.
                for k, v in keywords.items():
                    if cmd.startswith(k):
                        current_keyword = (k, v)
                        commands_string.append(cmd)
            else:
                # not match,`cmd` should be variable or command, so we
                # match variable here.
                statements.append(parse_shell_variables_and_command(cmd))
        else:
            # `commands_string` is not empty means we are in a loop or
            # branch, so we need to check end keyword.
            commands_string.append(cmd)
            if cmd.endswith(current_keyword[1]):
                statements.append(
                    parse_shell_loop_and_branch(
                        commands_string, current_keyword))
                commands_string = []
                current_keyword = ("", "")
    return statements


def parse_shell_variables_and_command(concatenated_command):
    '''given a concatenated command, classify the variable and command type,
    and then parse it '''
    # append white space at the end since we are matching white space for
    # the end of an assignment, and this white space will be removed by
    # clean_command()
    concatenated_command += ' '
    # pattern for matching variable, looking for '='
    # the second group first macthes a string assignment, if not, it will macth
    # until it first meets a white space
    assignment_pattern = r'([A-Za-z_][A-Za-z0-9_]*)=((".*")|(.*?)(?=[\s]))'
    export_pattern = r'^export ([A-Za-z_][A-Za-z0-9_]*)=(.*)'
    match_export = re.match(export_pattern, concatenated_command)
    match_assignment = re.finditer(assignment_pattern, concatenated_command)
    statement = {}
    # export_pattern matched
    if match_export:
        # assignment_pattern matched
        statement['variable'] = [{'name': match_export.group(1),
                                 'value': match_export.group(2)}]
    # check on assignment_pattern
    else:
        variable_list = []
        last_idx = 0
        # extract assignments
        for m in match_assignment:
            # variable assignment should be continous and start at the
            # beginning
            if len(concatenated_command[last_idx: m.span(0)[0]].strip()) > 0:
                continue
            variable_list.append({'name': m.group(1), 'value': m.group(2)})
            last_idx = m.span(0)[1]
        if variable_list:
            statement['variable'] = variable_list
        cleaned_command = clean_command(concatenated_command[last_idx:])
        # exists command after assignment OR begins with command
        if cleaned_command:
            statement['command'] = cleaned_command
    return statement


def parse_shell_loop_and_branch(commands_string, keyword_tuple):
    '''given a concatenated command, classify the loop and branch type,
    and then parse the loop '''
    loop_start_keywords = ['for', 'while']
    statement = {'content': commands_string}
    if keyword_tuple[0] in loop_start_keywords:
        statement['loop'] = {'type': keyword_tuple[0]}
        # extract commands between 'do' and 'done'
        loop_statements = []
        for cmd in commands_string:
            # 'loop_statements' is empty here, so we have not found 'do' yet.
            if not loop_statements:
                # find 'do', append to 'loop_statements'
                if cmd.startswith('do'):
                    # strip 'do' and whitespaces
                    cmd = cmd.lstrip('do ')
                    stat = parse_shell_variables_and_command(cmd)
                    loop_statements.append(stat)
            # 'loop_statements' is NOT empty here, we are in the statements now
            else:
                stat = parse_shell_variables_and_command(cmd)
                loop_statements.append(stat)
        # 'loop_statements' are ended with done, so we can just remove
        # the last statement which should be 'done;'
        loop_statements.pop()
        statement['loop'].update({'loop_statements': loop_statements})
    else:
        statement['branch'] = {'type': keyword_tuple[0]}
    return statement


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
    command_dict.update({'name': command_tokens.pop(0).strip()})
    # find options in the rest of the list
    while command_tokens:
        if options.match(command_tokens[0]):
            option_flag = command_tokens.pop(0).strip()
            # we have to check if this is the end of the command
            if command_tokens and not options.match(command_tokens[0]):
                option_arg = command_tokens[0].strip()
            else:
                option_arg = ''
            option_list.append((option_flag, option_arg))
        else:
            word_list.append(command_tokens.pop(0).strip())
    # now we have options and the remainder words
    command_dict.update({'options': option_list,
                         'words': word_list})
    return command_dict


def get_git_rev_or_version():
    '''Either get the current git commit or the PyPI distribution
    Use pbr to get the package version'''
    command = ['git', 'rev-parse', 'HEAD']
    try:
        output = subprocess.check_output(  # nosec
            command, stderr=subprocess.DEVNULL)
        if isinstance(output, bytes):
            output = output.decode('utf-8')
        ver_type = 'commit'

    except subprocess.CalledProcessError:
        ver_type = 'package'
        output = VersionInfo('tern').version_string()
    return ver_type, output.split('\n').pop(0)


def prop_names(obj):
    '''Given an object, return a generator that will produce the object's
    property key in its __dict__ representation and it's name'''
    for key in obj.__dict__:
        # remove private and protected decorator characters if any
        # first split on the dunder to get the class properties
        # then split on the first underscore to get the super class's
        # properties
        prop_name = key.split('__')[-1]
        if prop_name.startswith('_'):
            prop_name = prop_name[1:]
        yield key, prop_name


def check_tar(tar_file):
    '''Check if provided file is a valid tar archive file'''
    if os.path.exists(tar_file):
        if tarfile.is_tarfile(tar_file):
            return True
    return False


def check_root():
    '''Check to see if the current user is root or not. Return True if root
    and False if not'''
    if os.getuid() == 0:
        return True
    return False


def check_image_string(image_str: str):
    '''Check if the image string is in the format image:tag or
    image@digest_type:digest format. If not, return False.'''
    tag_format = r'.+:.+'
    digest_format = r'.+@.+:.+'
    if re.match(tag_format, image_str) or re.match(digest_format, image_str):
        return True
    return False


def parse_image_string(image_string):
    '''From the image string used to reference an image, return a dictionary
    of the form:
        {'name': <image name used (either from dockerhub or full name)>,
         'tag': <image tag>,
         'digest_type': <the hashing algorithm used>,
         'digest': <image digest>}
    per Docker's convention, an image can be referenced either as
    image OR image:tag OR image@hash:digest
    we choose ':' and '@' as separators
    Currently OCI also uses this convention'''
    tokens = re.split(r'[@:]', image_string)
    if len(tokens) == 1:
        return {'name': tokens[0],
                'tag': '',
                'digest_type': '',
                'digest': ''}
    if len(tokens) == 2:
        return {'name': tokens[0],
                'tag': tokens[1],
                'digest_type': '',
                'digest': ''}
    if len(tokens) == 3:
        return {'name': tokens[0],
                'tag': '',
                'digest_type': tokens[1],
                'digest': tokens[2]}
    if len(tokens) == 4:
        return {'name': tokens[0] + ":" + tokens[1],
                'tag': '',
                'digest_type': tokens[2],
                'digest': tokens[3]}
    return None
