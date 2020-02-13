# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import os
import random
import re
import tarfile
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


def get_top_dir():
    '''Get the hidden working directory'''
    return os.path.join(str(Path.home()), constants.dot_folder)


def initialize_names():
    randint = random.randint(10000, 99999)  # nosec
    constants.image = constants.image + "_" + str(randint)
    constants.tag = constants.tag + "_" + str(randint)
    constants.container = constants.container + "_" + str(randint)


def clean_command(command):
    '''Given a command string, clean out all whitespaces, tabs and line
    indentations
    Leave && alone'''
    return re.sub(cleaning, '', command).strip()


def split_command(command):
    '''Given a string of concatenated commands, return a list of commands'''
    return re.split(concat, command)


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
    prop_decorators = r'^__|^_'
    for key in obj.__dict__.keys():
        # remove private and protected decorator characters if any
        priv_name = '_' + obj.__class__.__name__
        prop_name = re.sub(priv_name, '', key)
        prop_name = re.sub(prop_decorators, '', prop_name, 1)
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
    return None
