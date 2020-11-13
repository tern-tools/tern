# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to process data returned from invoking retrieval commands
"""

import logging
import subprocess  # nosec

from tern.analyze.default.command_lib import command_lib
from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def get_snippet_list(invoke_step, work_dir=None, envs=None):
    """Given the invoke step dictionary i.e. steps of commands to run either
    in the chroot or on the host environment, get a list of command snippets
        invoke_dict: the value from the 'invoke' key
        workdir: If WORKDIR was set to anything, provide it here
        envs: If any environment variables were set, enter the key-value pairs
              here"""
    if 'container' in invoke_step.keys():
        snippet_list = invoke_step.get('container')
        # If environment variables exist, set them
        if envs:
            for var in envs:
                snippet_list.insert(
                    0, 'export ' + var.split('=')[0] + '=' + var.split('=')[1])
        # If work_dir exist cd into it
        if work_dir is not None:
            snippet_list.insert(0, 'cd ' + work_dir)
        return 'container', snippet_list
    return '', []


def invoke_in_rootfs(snippet_list, shell, package=''):
    '''Invoke the commands from the invoke dictionary in a root filesystem
    assuming the root filesystem is ready to accept commands'''
    # construct the full command
    full_cmd = command_lib.collate_snippets(snippet_list, package)
    try:
        result = rootfs.run_chroot_command(full_cmd, shell)
        try:
            result = result.decode('utf-8')
        except AttributeError:
            pass
        return result
    except subprocess.CalledProcessError as error:
        logger.warning('Error executing snippets: %s', error)
        raise


def get_pkg_attrs(attr_dict, shell, work_dir=None, envs=None, package_name=''):
    """Given the dictionary containing the steps to invoke either in
    the container or on the host, invoke the steps and return the results
    either in list form or in raw form"""
    error_msgs = ''
    # the invoke dictionary contains steps
    # for each step make a command to invoke
    # currently we only deal with 1 step
    # so we just return the last step's results
    result = ""
    if 'invoke' in attr_dict.keys():
        for step in range(1, len(attr_dict['invoke'].keys()) + 1):
            method, snippet_list = get_snippet_list(
                attr_dict['invoke'][step], work_dir, envs)
            if method == 'container':
                # invoke the snippet list in a chroot environment
                try:
                    result = invoke_in_rootfs(
                        snippet_list, shell, package=package_name)
                    result = result[:-1]
                except subprocess.CalledProcessError as error:
                    error_msgs = error_msgs + error.stderr
    if 'delimiter' in attr_dict.keys():
        res_list = result.split(attr_dict['delimiter'])
        if res_list[-1] == '':
            res_list.pop()
            return res_list, error_msgs
        return res_list, error_msgs
    # if there is no delimiter, return the result string
    return result, error_msgs


def collect_list_metadata(shell, listing, work_dir=None, envs=None):
    '''Given the shell and the listing for the package manager, collect
    metadata that gets returned as a list'''
    pkg_dict = {}
    msgs = ''
    warnings = ''
    # a valid shell needs to exist in the filesystem for this to work
    for item in command_lib.base_keys:
        # check if the supported items exist in the given listing
        if item in listing.keys():
            items, msg = get_pkg_attrs(listing[item], shell, work_dir, envs)
            msgs = msgs + msg
            if item == 'files':
                # convert this data into a list before adding it to the
                # package dictionary
                file_list = []
                for files_str in items:
                    # convert the string into a list
                    files = []
                    for filepath in filter(bool, files_str.split('\n')):
                        files.append(filepath.lstrip('/'))
                    file_list.append(files)
                pkg_dict.update({item: file_list})
            else:
                pkg_dict.update({item: items})
        else:
            warnings = warnings + errors.no_listing_for_base_key.format(
                listing_key=item)
    return pkg_dict, msgs, warnings
