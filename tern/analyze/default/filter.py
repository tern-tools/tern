# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to categorize commands into install, remove and ignore commands
"""


import logging
import re

from tern.analyze.default.command_lib import command_lib
from tern.analyze import common
from tern.report import formats
from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)


def get_installed_package_names(command):
    '''Given a Command object, return a list of package names'''
    pkgs = []
    # check if the command attributes are set
    if command.is_set() and command.is_install():
        for word in command.words:
            pkgs.append(word)
    return pkgs


def remove_ignored_commands(command_list):
    '''For a list of Command objects, examine if the command is ignored.
    Return all the ignored command strings. This is a filtering operation
    so all the ignored command objects will be removed from the original
    list'''
    ignore_commands = ''
    filtered_list = []
    while command_list:
        command = command_list.pop(0)
        if command.is_set() and command.is_ignore():
            ignore_commands = ignore_commands + command.shell_command + '\n'
        else:
            filtered_list.append(command)
    return ignore_commands, filtered_list


def remove_unrecognized_commands(command_list):
    '''For a list of Command objects, examine if the command is not recognized.
    Return all the unrecognized command strings. This is a filtering operation
    so all the unrecognized command objects will be removed from the original
    list'''
    unrec_commands = ''
    filtered_list = []
    while command_list:
        command = command_list.pop(0)
        if not command.is_set():
            unrec_commands = unrec_commands + command.shell_command + '\n'
        else:
            filtered_list.append(command)
    return unrec_commands, filtered_list


def consolidate_commands(command_list):
    '''Given a list of Command objects, consolidate the install and remove
    commands into one install command and return a list of resulting
    command objects'''
    new_list = []

    if len(command_list) == 1:
        new_list.append(command_list.pop(0))

    while command_list:
        # match the first command with its following commands.
        first = command_list.pop(0)
        for _ in range(0, len(command_list)):
            second = command_list.pop(0)
            if first.is_remove() and second.is_install():
                # if remove then install, ignore the remove command
                new_list.append(second)
            else:
                if not first.merge(second):
                    # Unable to merge second, we should keep second command.
                    command_list.append(second)
        # after trying to merge with all following commands, add first command
        # to the new_dict.
        new_list.append(first)
    return new_list


def filter_install_commands(shell_command_line):
    '''Given a shell command line:
        1. Create a list of Command objects
        2. For each command, check against the command library for installed
        commands
        3. Return installed command objects, and messages for ignored commands
        and unrecognized commands'''
    report = ''
    command_list, branch_report = common.get_shell_commands(shell_command_line)
    for command in command_list:
        command_lib.set_command_attrs(command)
    ignore_msgs, filter1 = remove_ignored_commands(command_list)
    unrec_msgs, filter2 = remove_unrecognized_commands(filter1)
    if ignore_msgs:
        report = report + formats.ignored + ignore_msgs
    if unrec_msgs:
        report = report + formats.unrecognized + unrec_msgs
    if branch_report:
        report = report + branch_report
    return consolidate_commands(filter2), report


def get_run_command(value):
    """A general function to return the command line that created a layer
    given the value of some metadata key from the container image"""
    # we check for '/bin/sh -c' in the value
    if '/bin/sh -c' in value:
        return re.sub('/bin/sh -c ', '', value).strip()
    return ''
