# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Docker specific functions - used when trying to retrieve packages when
given a Dockerfile
"""
import logging
import os
import re
import subprocess  # nosec

from tern.classes.docker_image import DockerImage
from tern.classes.notice import Notice
from tern.utils import dockerfile
from tern.utils import container
from tern.utils import constants
from tern.report import errors
from tern.report import formats
from tern import common

# dockerfile
dockerfile_global = ''
# dockerfile commands
docker_commands = []

# global logger
logger = logging.getLogger(constants.logger_name)


def load_docker_commands(dockerfile_path):
    '''Given a dockerfile get a persistent list of docker commands'''
    if not os.path.isfile(dockerfile_path):
        raise IOError('{} does not exist'.format(dockerfile_path))
    global docker_commands
    docker_commands = dockerfile.get_directive_list(
        dockerfile.get_command_list(dockerfile_path))
    global dockerfile_global
    dockerfile_global = dockerfile_path


def print_dockerfile_base(base_instructions):
    '''For the purpose of tracking the lines in the dockerfile that
    produce packages, return a string containing the lines in the dockerfile
    that pertain to the base image'''
    base_instr = ''
    for instr in base_instructions:
        base_instr = base_instr + instr[0] + ' ' + instr[1]
    return base_instr


def get_dockerfile_base():
    '''Get the base image object from the dockerfile base instructions
    1. get the instructions around FROM
    2. get the base image and tag
    3. Make notes based on what the image and tag rules are
    4. Return an image object and the base instructions string'''
    try:
        base_instructions = dockerfile.get_base_instructions(docker_commands)
        base_image_tag = dockerfile.get_base_image_tag(base_instructions)
        dockerfile_lines = print_dockerfile_base(base_instructions)
        # check for scratch
        if base_image_tag[0] == 'scratch':
            # there is no base image - return no image object
            return None
        # there should be some image object here
        repotag = base_image_tag[0] + dockerfile.tag_separator + \
            base_image_tag[1]
        from_line = 'FROM ' + repotag
        base_image = DockerImage(repotag)
        base_image.origins.add_notice_origin(dockerfile_lines)
        base_image.name = base_image_tag[0]
        # check if there is a tag
        if not base_image_tag[1]:
            message_string = errors.dockerfile_no_tag.format(
                dockerfile_line=from_line)
            base_image.origins.add_notice_to_origins(
                dockerfile_lines, Notice(message_string, 'warning'))
            base_image.tag = 'latest'
        else:
            base_image.tag = base_image_tag[1]
        # check if the tag is 'latest'
        if base_image_tag[1] == 'latest':
            message_string = errors.dockerfile_using_latest.format(
                dockerfile_line=from_line)
            base_image.origins.add_notice_to_origins(
                dockerfile_lines, Notice(message_string, 'warning'))
        return base_image, dockerfile_lines
    except ValueError as e:
        logger.warning("%s", errors.cannot_parse_base_image.format(
            dockerfile=dockerfile_global, error_msg=e))
        return None


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
    except subprocess.CalledProcessError as error:
        print(errors.docker_build_failed.format(
            dockerfile=dockerfile_global, error_msg=error.output))
        success = False
        logger.error('Error building image: %s', error.output)
        msg = error.output
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
    else:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.no_created_by, 'warning'))
    command_line = instruction.split(' ', 1)[1]
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
    dockerfile_lines = dockerfile.get_command_list(dockerfile_global)
    index = -1
    from_line = ''
    for line in dockerfile_lines:
        if 'FROM' in line:
            from_line = line
            break
    for layer in docker_image.layers:
        instr = created_to_instruction(layer.created_by)
        if instr in dockerfile_lines:
            index = docker_image.layers.index(layer)
            break
    if index != -1:
        # index was set so all layers before this index has been imported
        for i in range(0, index):
            docker_image.layers[i].import_str = from_line
