# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Docker specific functions - used when trying to retrieve packages when
given a Dockerfile
"""
import logging
import os
import re
import sys

from tern.classes.docker_image import DockerImage
from tern.classes.notice import Notice
from tern.utils import constants
from tern.utils import general
from tern.report import errors
from tern.report import formats
from tern.analyze.default import filter as fltr
from tern.analyze.default.command_lib import command_lib
from tern.analyze.default.dockerfile import parse
from tern.utils.general import check_image_string

# dockerfile
dockerfile_global = ''
# dockerfile commands
docker_commands = []

# global logger
logger = logging.getLogger(constants.logger_name)


def load_docker_commands(dfobj):
    '''Given a dockerfile object get a persistent list of docker commands'''
    if not os.path.isfile(dfobj.filepath):
        raise IOError('{} does not exist'.format(dfobj.filepath))
    global docker_commands
    docker_commands = dfobj.structure
    global dockerfile_global
    dockerfile_global = dfobj.filepath


def get_dockerfile_base():
    '''Get the base image object from the dockerfile base instructions
    1. get the instructions around FROM
    2. get the base image and tag
    3. Make notes based on what the image and tag rules are
    4. Return an image object and the base instructions string
    NOTE: Potential ARG values in the Dockerfile object have already been
    expanded at this point. However, Dockerfile rules say that if no
    --build-arg is passed during docker build and ARG has no default, the
    build will fail. We assume for now that we will not be passing build
    arguments in which case if there is no default ARG, we will raise an
    exception indicating that since the build arguments are determined by
    the user we will not be able to determine what the user wanted'''
    try:
        # Get the base image tag.
        # NOTE: ARG values have already been expanded.
        base_image_string, from_line = get_base_image_tag(docker_commands)
        # check for scratch
        if base_image_string == 'scratch':
            # there is no base image to pull
            raise ValueError("Cannot pull 'scratch' base image.")
        # there should be some image object here
        base_image = DockerImage(base_image_string)
        base_image.origins.add_notice_origin(from_line)
        base_image.name = base_image_string.split(':')[0]
        # check if there is a tag
        if not check_image_string(base_image_string):
            message_string = errors.dockerfile_no_tag.format(
                dockerfile_line=from_line)
            base_image.origins.add_notice_to_origins(
                docker_commands, Notice(message_string, 'warning'))
            base_image.tag = 'latest'
        else:
            base_image.tag = base_image_string.split(':')[1]
        # check if the tag is 'latest'
        if base_image.tag == 'latest':
            message_string = errors.dockerfile_using_latest.format(
                dockerfile_line=from_line)
            base_image.origins.add_notice_to_origins(
                docker_commands, Notice(message_string, 'warning'))
        return base_image, from_line
    except ValueError as e:
        logger.fatal("%s", errors.cannot_parse_base_image.format(
            dockerfile=dockerfile_global, error_msg=e))
        sys.exit(1)


def get_base_image_tag(dockerfile_lines):
    '''Get the instructions around FROM, return the base image string
    and the line containing FROM command'''
    base_image_string = ''
    from_line = ''
    for i, cmd_dict in enumerate(dockerfile_lines):
        if cmd_dict['instruction'] == 'FROM':
            # Account for "as" keyword in FROM line
            base_image_string = re.split(" as", cmd_dict['value'],
                                         flags=re.IGNORECASE)[0]
            from_line = 'FROM' + base_image_string
            # Check that potential ARG values has default
            if i != 0 and dockerfile_lines[i - 1]['instruction'] == 'ARG':
                if len(dockerfile_lines[i - 1]['value'].split('=')) == 1:
                    raise ValueError('No ARG default value to pass to '
                                     'FROM command in Dockerfile.')
            break
    return base_image_string, from_line


def get_dockerfile_image_tag():
    '''Return the image and tag used to build an image from the dockerfile'''
    image_tag_string = constants.image + parse.tag_separator + \
        constants.tag
    return image_tag_string


def created_to_instruction(created_by):
    '''The 'created_by' key in a Docker image config gives the shell
    command that was executed unless it is a #(nop) instruction which is
    for the other Docker directives. Convert this line into a Dockerfile
    instruction'''
    instruction = re.sub('/bin/sh -c ', '', created_by).strip()
    instruction = re.sub(re.escape('#(nop) '), '', instruction).strip()
    first = instruction.split(' ').pop(0)
    if first and first not in parse.directives and \
            'RUN' not in instruction:
        instruction = 'RUN ' + instruction
    return instruction


def get_commands_from_history(image_layer):
    '''Given the image layer object and the shell, get the list of command
    objects that created the layer'''
    # set up notice origin for the layer
    origin_layer = 'Layer {}'.format(image_layer.layer_index)
    if image_layer.created_by:
        instruction = created_to_instruction(image_layer.created_by)
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.dockerfile_line.format(dockerfile_instruction=instruction),
            'info'))
        command_line = instruction.split(' ', 1)[1]
    else:
        instruction = ''
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.no_created_by, 'warning'))
        command_line = instruction
    # Image layers are created with the directives RUN, ADD and COPY
    # For ADD and COPY instructions, there is no information about the
    # packages added
    if 'ADD' in instruction or 'COPY' in instruction:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            errors.unknown_content.format(files=command_line), 'warning'))
        # return an empty list as we cannot find any commands
        return []
    # for RUN instructions we can return a list of commands
    command_list, msg = fltr.filter_install_commands(command_line)
    if msg:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            msg, 'warning'))
    return command_list


def set_imported_layers(docker_image):
    '''Given a Docker image object that was built from a Dockerfile, set the
    layers that were imported using the Dockerfile's FROM command or the ones
    that came before it'''
    index = -1
    from_line = ''
    dockerfile_lines = docker_commands
    for cmd in dockerfile_lines:
        if cmd['instruction'] == 'FROM':
            from_line = cmd['content'].rstrip()
            break
    command_list = parse.get_command_list(dockerfile_lines)
    for layer in docker_image.layers:
        instr = created_to_instruction(layer.created_by)
        if instr in command_list:
            index = docker_image.layers.index(layer)
            break
    if index != -1:
        # index was set so all layers before this index has been imported
        for i in range(0, index - 1):
            docker_image.layers[i].import_str = from_line


def get_env_vars(image_obj):
    '''Given a docker image object, return the list of environment variables,
    if any, based on their values in the config.'''
    config = image_obj.get_image_config(image_obj.get_image_manifest())
    # replace '\t' with '\\t'  in the ENV
    for idx, env_str in enumerate(config['config']['Env']):
        config['config']['Env'][idx] = env_str.replace('\t', '\\t')
    return config['config']['Env']


def lock_layer_instruction(dfobj, line_index, commands, image_layer):
    """Given the Dockerfile object, the line index that we are replacing,
    the list command objects that installed packages, and the image layer,
    rewrite the corresponding line in the Dockerfile with the package and
    the version installed"""
    for command in commands:
        # get the version separator
        vsep = command_lib.check_pinning_separator(command.name)
        # replace the packages with package separators for each of the words
        for word in command.words:
            for pkg in image_layer.packages:
                if pkg.name == word:
                    parse.expand_package(
                        dfobj.structure[line_index], pkg.name, pkg.version,
                        vsep)
    return dfobj


def lock_dockerfile(dfobj, image_obj):
    """Given a Dockerfile object and the corresponding Image object, rewrite
    the content to pin packages to their versions"""
    # get all the RUN commands in the dockerfile
    run_list = parse.get_run_layers(dfobj)
    # go through the image layers to find the ones corresponding to the
    # run commands
    for layer in image_obj.layers:
        if not layer.import_str:
            # this layer is not from a FROM line
            # we get the layer instruction
            cmd, instr = fltr.get_run_command(layer.created_by)
            if instr == 'RUN':
                # find the line in the Dockerfile that matches this command
                for run_dict in run_list:
                    if run_dict['value'] == cmd:
                        # get the list of install commands
                        command_list, _ = fltr.filter_install_commands(
                            general.clean_command(run_dict['value']))
                        # pin packages installed by each command
                        run_index = dfobj.structure.index(run_dict)
                        dfobj = lock_layer_instruction(
                            dfobj, run_index, command_list, layer)
    return dfobj


def create_locked_dockerfile(dfobj):
    '''Given a dockerfile object, the information in a new Dockerfile object
    Copy the dfobj info to the destination output Dockerfile location'''
    # packages in RUN lines, ENV, and ARG values are already expanded
    parse.expand_add_command(dfobj)
    # create the output file
    dfile = ''
    prev_endline = 0
    for command_dict in dfobj.structure:
        endline = command_dict["endline"]
        diff = endline - prev_endline
        # calculate number of new line characters to
        # add before each line of content
        delimeter = "\n" * (diff - 1) if diff > 1 else ""
        dfile = dfile + delimeter + command_dict['content']
        prev_endline = endline
    return dfile


def write_locked_dockerfile(dfile, destination=None):
    '''Write the pinned Dockerfile to a file'''
    if destination is not None:
        file_name = destination
    else:
        file_name = constants.locked_dockerfile
    with open(file_name, 'w') as f:
        f.write(dfile)
