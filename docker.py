'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''
import logging
import subprocess

from classes.docker_image import DockerImage
from classes.notice import Notice
from classes.command import Command
from utils import dockerfile as df
from utils import container as cont
from utils import constants as const
from report import errors
from report import formats
from command_lib import command_lib as cmdlib
import common

'''
Docker specific functions - used when trying to retrieve packages when
given a Dockerfile
'''

# dockerfile
dockerfile = ''
# dockerfile commands
docker_commands = []

# global logger
logger = logging.getLogger('docker.py')


def load_docker_commands(dockerfile_path):
    '''Given a dockerfile get a persistent list of docker commands'''
    global docker_commands
    docker_commands = df.get_directive_list(df.get_command_list(
        dockerfile_path))
    global dockerfile
    dockerfile = dockerfile_path


def print_dockerfile_base():
    '''For the purpose of tracking the lines in the dockerfile that
    produce packages, return a string containing the lines in the dockerfile
    that pertain to the base image'''
    base_instr = ''
    for instr in df.get_base_instructions(docker_commands):
        base_instr = base_instr + instr[0] + ' ' + instr[1] + '\n'
    return base_instr


def get_dockerfile_base():
    '''Get the base image object from the dockerfile base instructions
    1. get the instructions around FROM
    2. get the base image and tag
    3. Make notes based on what the image and tag rules are
    4. Return an image object'''
    try:
        base_instructions = df.get_base_instructions(docker_commands)
        base_image_tag = df.get_base_image_tag(base_instructions)
        # check for scratch
        if base_image_tag[0] == 'scratch':
            # there is no base image - return no image object
            return None
        # there should be some image object here
        repotag = base_image_tag[0] + df.tag_separator + base_image_tag[1]
        from_line = 'FROM ' + repotag
        origin = print_dockerfile_base(base_instructions)
        base_image = DockerImage(repotag)
        base_image.name = base_image_tag[0]
        # check if there is a tag
        if not base_image_tag[1]:
            message_string = errors.dockerfile_no_tag.format(
                dockerfile_line=from_line)
            no_tag_notice = Notice()
            no_tag_notice.origin = origin
            no_tag_notice.message = message_string
            no_tag_notice.level = 'warning'
            base_image.notices.add_notice(no_tag_notice)
            base_image.tag = 'latest'
        else:
            base_image.tag = base_image_tag[1]
        # check if the tag is 'latest'
        if base_image_tag[1] == 'latest':
            message_string = errors.dockerfile_using_latest.format(
                dockerfile_line=from_line)
            latest_tag_notice = Notice()
            latest_tag_notice.origin = origin
            no_tag_notice.message = message_string
            no_tag_notice.level = 'warning'
            base_image.notices.add_notice(latest_tag_notice)
        return base_image
    except ValueError as e:
        logger.warning(errors.cannot_parse_base_image.format(
            dockerfile=dockerfile, error_msg=e))
        return None


def get_dockerfile_image_tag():
    '''Return the image and tag used to build an image from the dockerfile'''
    image_tag_string = const.image + df.tag_separator + const.tag
    return image_tag_string


def is_build():
    '''Attempt to build a given dockerfile
    If it does not build return False. Else return True'''
    image_tag_string = get_dockerfile_image_tag()
    success = False
    msg = ''
    try:
        cont.build_container(dockerfile, image_tag_string)
    except subprocess.CalledProcessError as error:
        print(errors.docker_build_failed.format(
            dockerfile=dockerfile, error_msg=error.output))
        success = False
        msg = error.output
    else:
        success = True
    return success, msg


def get_shell_commands(run_instruction):
    '''Given a RUN command return a list of shell commands to be run'''
    comm_list = run_instruction.split('&&')
    cleaned_list = []
    for comm in comm_list:
        cleaned_list.append(Command(comm.strip()))
    return cleaned_list


def get_packages_per_run(run_instruction):
    '''Given a dockerfile run instruction:
        1. Create a list of Command objects
        2. For each command, check against the command library for installed
        commands
        3. For each install command get installed packages
        4. Return installed packages and messages for ignored commands and
        unrecognized commands'''
    command_list = get_shell_commands(run_instruction)
    for command in command_list:
        cmdlib.set_command_attrs(command)
    ignore_msgs, filter1 = common.remove_ignored_commands(command_list)
    unrec_msgs, filter2 = common.remove_unrecognized_commands(filter1)
    pkg_list = []
    for command in filter2:
        pkg_list.extend(common.get_installed_packages(command))
    report = formats.ignored + ignore_msgs + formats.unrecognized + unrec_msgs
    return pkg_list, report
