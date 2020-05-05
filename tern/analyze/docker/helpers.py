# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Docker specific functions - used when trying to retrieve packages when
given a Dockerfile
"""
import docker
import logging
import os
import re
import sys

from tern.classes.docker_image import DockerImage
from tern.classes.notice import Notice
from tern.analyze.docker import dockerfile
from tern.analyze.docker import container
from tern.utils import constants
from tern.report import errors
from tern.report import formats
from tern.analyze import common
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
            if i != 0 and dockerfile_lines[i-1]['instruction'] == 'ARG':
                if len(dockerfile_lines[i-1]['value'].split('=')) == 1:
                    raise ValueError('No ARG default value to pass to '
                                     'FROM command in Dockerfile.')
            break
    return base_image_string, from_line


def get_dockerfile_image_tag():
    '''Return the image and tag used to build an image from the dockerfile'''
    image_tag_string = constants.image + dockerfile.tag_separator + \
        constants.tag
    return image_tag_string


def is_build():
    '''Attempt to build a given dockerfile
    If it does not build return False. Else return True'''
    image_tag_string = get_dockerfile_image_tag()
    success = False
    msg = ''
    try:
        container.build_container(dockerfile_global, image_tag_string)
    except (docker.errors.APIError, docker.errors.BuildError) as error:
        success = False
        logger.error('Error building image: %s', str(error))
        msg = str(error)
    else:
        logger.debug('Successfully built image')
        success = True
    return success, msg


def created_to_instruction(created_by):
    '''The 'created_by' key in a Docker image config gives the shell
    command that was executed unless it is a #(nop) instruction which is
    for the other Docker directives. Convert this line into a Dockerfile
    instruction'''
    instruction = re.sub('/bin/sh -c ', '', created_by).strip()
    instruction = re.sub(re.escape('#(nop) '), '', instruction).strip()
    first = instruction.split(' ').pop(0)
    if first and first not in dockerfile.directives and \
            'RUN' not in instruction:
        instruction = 'RUN ' + instruction
    return instruction


def get_commands_from_history(image_layer):
    '''Given the image layer object and the shell, get the list of command
    objects that created the layer'''
    # set up notice origin for the layer
    origin_layer = 'Layer: ' + image_layer.fs_hash[:10]
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
    command_list, msg = common.filter_install_commands(command_line)
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
    command_list = dockerfile.get_command_list(dockerfile_lines)
    for layer in docker_image.layers:
        instr = created_to_instruction(layer.created_by)
        if instr in command_list:
            index = docker_image.layers.index(layer)
            break
    if index != -1:
        # index was set so all layers before this index has been imported
        for i in range(0, index):
            docker_image.layers[i].import_str = from_line
