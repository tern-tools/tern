# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Dockerfile information retrieval and modification
"""

from dockerfile_parse import DockerfileParser
import re
import logging

from tern.utils import general
from tern.utils import constants
from tern.analyze import common
from tern.analyze.default.command_lib import command_lib

# global logger
logger = logging.getLogger(constants.logger_name)

directives = ['FROM',
              'ARG',
              'ADD',
              'ENV',
              'COPY',
              'ENTRYPOINT',
              'WORKDIR',
              'VOLUME',
              'EXPOSE',
              'CMD']

# regex for matching lines in a dockerfile
comments = re.compile('^#')
line_indent = re.compile('.*\\\\$')
tabs = re.compile('\t')

# regex strings
bash_var = R'[\$\{\}]'

# strings
tag_separator = ':'


class Dockerfile():
    ''' This class is used as a wrapper to store dockerfile information
    retrieved from the parser.'''

    def __init__(self):
        self.structure = None
        self.envs = None
        self.prev_env = None
        self.filepath = ""
        self.parent_images = []

    def is_none(self):
        """Check if the object is empty."""
        is_none = True
        if (self.structure or
                self.envs or
                self.prev_env or
                self.filepath):
            is_none = False
        return is_none


def get_dockerfile_obj(dockerfile_name, prev_env=None):
    '''Given a Dockerfile, create a Dockerfile parser object to be used later.
    dockerfile_name: This is the path to the Dockerfile including the
                            file name
    prev_env: These are environment variables that may have been used in
    previous stages in a multistage docker build. Should be a python dictionary
    of the form {'ENV': 'value',...}'''
    dfobj = Dockerfile()
    with open(dockerfile_name) as f:
        parser = DockerfileParser(parent_env=prev_env, fileobj=f)
        dfobj.filepath = dockerfile_name
        dfobj.structure = parser.structure
        dfobj.envs = parser.envs
        dfobj.prev_env = prev_env
        dfobj.parent_images = parser.parent_images
        dfobj.is_multistage = parser.is_multistage
    return dfobj


def replace_env(key_value_dict, df_structure_dict):
    '''Replace the environment variables in the key_value_dict dictionary
    with its corresponding value in the df_line_dict dictionary
    key_value_dict: a dictionary of key-value pairs like envs in the dockerfile
                    object
    df_structure_dict: a dictionary from the dockerfile object's structure'''
    for key, val in key_value_dict.items():
        envvar1 = '$' + key
        envvar2 = '${' + key + '}'
        df_structure_dict['content'] = df_structure_dict['content'].replace(
            envvar1, val)
        df_structure_dict['content'] = df_structure_dict['content'].replace(
            envvar2, val)
        df_structure_dict['value'] = df_structure_dict['value'].replace(
            envvar1, val)
        df_structure_dict['value'] = df_structure_dict['value'].replace(
            envvar2, val)


def expand_vars(dfobj):
    '''Replace the environment variables with their values if known
    dfobj: the Dockerfile object created using get_dockerfile_obj'''
    if dfobj.envs:
        for obj in dfobj.structure:
            replace_env(dfobj.envs, obj)
    if dfobj.prev_env:
        for obj in dfobj.structure:
            replace_env(dfobj.prev_env, obj)


def expand_arg(dfobj):
    '''Replace the ARG variables with their values if known
    dfobj: the Dockerfile object created using get_dockerfile_obj'''
    # get arg dictionary
    arg_dict = {}
    for instruction_desc in dfobj.structure:
        if instruction_desc['instruction'] == 'ARG':
            instruction_value_split = instruction_desc['value'].split('=')
            # contains '='
            if len(instruction_value_split) == 2:
                key = instruction_value_split[0].strip(' ')
                value = instruction_value_split[1].strip(' ')
                arg_dict[key] = value
    # expand arg variables
    if arg_dict:
        for obj in dfobj.structure:
            replace_env(arg_dict, obj)
    # Update dfobj parent image just in case ARG value was used in FROM line
    update_parent_images(dfobj)


def update_parent_images(dfobj):
    '''Given a Dockerfile object, update the parent_images list. This function
    will be useful after ARG values have been replaced in expand_arg() that
    can sometimes affect the FROM line(s) of a Dockerfile.'''
    new_parent_list = []
    for cmd_dict in dfobj.structure:
        if cmd_dict['instruction'] == 'FROM':
            new_parent_list.append(re.split(" as", cmd_dict['value'],
                                            flags=re.IGNORECASE)[0])
    dfobj.parent_images = new_parent_list


def parse_from_image(dfobj):
    '''Get a list of dictionaries from the FROM instruction. The dictionary
    should be of the form:
        [{'name': <image name used (either from dockerhub or full name)>,
          'tag': <image tag>,
          'digest_type': <the hashing algorithm used>
          'digest': <image digest>}..]'''
    image_list = []
    for image_string in dfobj.parent_images:
        image_list.append(general.parse_image_string(image_string))
    return image_list


def expand_from_images(dfobj, image_list):
    '''Update the structure dictionary with the 'import_str'
    value of images.

    dfobj: the Dockerfile object created using get_dockerfile_obj
    '''
    if not dfobj.is_multistage:
        return

    image_count = 0
    # keep import_str of first image as a default value
    import_str = image_list[0].layers[0].import_str
    for index, command_dict in enumerate(dfobj.structure):
        if command_dict['instruction'] == 'FROM':
            # if import_str is not set for the image then take a default value
            if len(image_list[image_count].layers) > 0 and \
                    image_list[image_count].layers[0].import_str:
                import_str = image_list[image_count].layers[0].import_str
            if command_dict['instruction'] in import_str:
                dfobj.structure[index]['content'] = import_str + '\n'
            else:
                dfobj.structure[index]['content'] = command_dict['instruction'] + \
                    ' ' + import_str + '\n'
            image_count += 1


def should_pin(run_line, package, index):
    '''This check is necessary to make sure that commands that double as
    packages (i.e. language package managers like pip, gem) are pinned properly
    in a locked dockerfile. For example, in the RUN line "pip install pkg"
    we would not pin 'pip' to its version, but if the line was
    "apt install pip" then we would want to pin the version.
    Return True if the package should be pinned, return False if it
    should not.'''
    if package not in command_lib.command_lib['snippets'].keys():
        return True
    if index < 1:
        return False
    if index < len(run_line) + 1:
        if run_line[index + 1] == \
                command_lib.command_lib['snippets'][package]['install']:
            return False
    return True


def expand_package(command_dict, package, version, pinning_separator):
    '''Update the given dockerfile object with the pinned package
    and version information. '''
    sub_string = ''
    for i, word in enumerate(command_dict['value'].split()):
        # only pin if the package word is not the install directive
        if word == package and should_pin(command_dict['value'].split(),
                                          word, i):
            sub_string += word + pinning_separator + version + ' '
        else:
            sub_string += word + ' '
    command_dict['value'] = sub_string
    # Update 'content' to match 'value' in dfobj
    command_dict['content'] = command_dict['instruction'] + ' ' + \
        command_dict['value'] + '\n'


def get_run_layers(dfobj):
    '''Given a dockerfile object, collect a list of RUN command dictionaries'''
    run_list = []
    for command_dict in dfobj.structure:
        if command_dict['instruction'] == 'RUN':
            run_list.append(command_dict)
    return run_list


def get_install_packages(command_dict):
    '''Given a dockerfile RUN line, return a list of packages to be
    installed from that line.'''
    command_words, _ = common.filter_install_commands(command_dict['value'])
    install_packages = []
    for command in command_words:
        for word in command.words:
            install_packages.append(word)
    return install_packages


def get_command_list(dfobj_structure):
    '''Given a dockerfile object structure, return the list of commands
    from the list of dictionaries. Useful when you don't want to loop
    through the dictionary for commands'''
    cmd_list = []
    for cmd_dict in dfobj_structure:
        if cmd_dict['instruction'] != 'COMMENT':
            cmd_list.append(cmd_dict['content'].rstrip())
    return cmd_list


def find_git_info(line, dockerfile_path):
    '''Given a line of ADD command and the path of dockerfile,
    return the information(string format) on the git project name and sha
    if the dockerfile is included in a git repository.
    ADD command has a general format:
    ADD [--chown=<user>:<group>] <src> <dst>
    Currently we parse the <src>, but not use it.
    '''
    args = line.split(' ')
    src_path = ''
    # check if --chown exists
    if args[1].startswith('--chown'):
        # check if the line is valid
        if len(args) < 4:
            logger.error('Invalid ADD command line')
        src_path = args[2]
    else:
        # the line has no --chown option
        if len(args) < 3:
            logger.error('Invalid ADD command line')
        src_path = args[1]
    # log the parsed src_path
    logger.debug('Parsed src_path is %s', src_path)
    # get the git project info
    comment_line = common.check_git_src(dockerfile_path)
    # get the git project link
    url_list = common.get_git_url(dockerfile_path)
    if url_list:
        comment_url = ', '.join(url_list)
        comment_line += ', project url(s): ' + comment_url
    return comment_line


def expand_add_command(dfobj):
    dockerfile_path = dfobj.filepath
    for i, command_dict in enumerate(dfobj.structure):
        if command_dict['instruction'] in ['ADD', 'COPY']:
            comment_line = find_git_info(command_dict['content'],
                                         dockerfile_path)
            dfobj.structure[i]['content'] = \
                command_dict['content'].strip('\n') + \
                ' # ' + comment_line + '\n'
            dfobj.structure[i]['value'] = command_dict['value']\
                + ' # ' + comment_line


def get_from_indices(dfobj):
    """Given a dockerfile object, return the indices of FROM lines
    in the dfobj structure."""
    from_lines = []
    for idx, st in enumerate(dfobj.structure):
        if st['instruction'] == 'FROM':
            from_lines.append(idx)
    from_lines.append(len(dfobj.structure))
    return from_lines


def get_dockerfile_stages(dfobj_multi):
    """Given a multistage dockerfile object, return a list of content for
    each stage"""
    stages = []
    from_lines = get_from_indices(dfobj_multi)
    # Pop the first FROM
    start_line = from_lines.pop(0)
    while len(from_lines) >= 1:
        stage = ""
        end_line = from_lines[0]
        for idx in range(start_line, end_line):
            if dfobj_multi.structure[idx]['instruction'] != 'COMMENT':
                stage = stage + dfobj_multi.structure[idx]['content']
        stages.append(stage)
        start_line = from_lines.pop(0)
    return stages
