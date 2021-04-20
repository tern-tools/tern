# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to process data returned from invoking retrieval commands
"""

import logging
import subprocess  # nosec

from tern.analyze.default.command_lib import command_lib
from tern.analyze.default.live import collect as lcol
from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def get_snippet_list(invoke_step, prereqs):
    """Given the invoke step dictionary i.e. steps of commands to run either
    in the chroot or on the host environment, get a list of command snippets
        invoke_dict: the value from the 'invoke' key
        workdir: If WORKDIR was set to anything, provide it here
        envs: If any environment variables were set, enter the key-value pairs
              here"""
    if 'container' in invoke_step.keys():
        snippet_list = invoke_step.get('container')
        # If environment variables exist, set them
        if prereqs.envs:
            for var in prereqs.envs:
                snippet_list.insert(
                    0, 'export ' + var.split('=')[0] + '=\"' + var.split('=')[1] + '\"')
        # If work_dir exist cd into it
        if prereqs.layer_workdir:
            snippet_list.insert(0, 'cd ' + prereqs.layer_workdir)
        return 'container', snippet_list
    if 'host' in invoke_step.keys():
        snippet_list = invoke_step.get('host')
        # we would expect to cd into the layer's host path
        snippet_list.insert(0, 'cd ' + prereqs.host_path)
        return 'host', snippet_list
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


def invoke_on_host(snippet_list, shell, package=""):
    '''Invoke the commands from the invoke dictionary in an unpacked
    root filesystem'''
    # construct the full command
    full_cmd = command_lib.collate_snippets(snippet_list, package)
    try:
        result = rootfs.run_host_command(full_cmd, shell)
        try:
            result = result.decode("utf-8")
        except AttributeError:
            pass
        return result
    except subprocess.CalledProcessError as error:
        logger.warning("Error executing snippets: %s", error)
        raise


def invoke_in_rootfs_wrapped(snippet_list, shell, package=""):
    error_msgs = ''
    result = ''
    try:
        result = invoke_in_rootfs(snippet_list, shell, package)
        result = result[:-1]
    except subprocess.CalledProcessError as error:
        error_msgs = error_msgs + error.stderr
    return result, error_msgs


def invoke_on_host_wrapped(snippet_list, shell, package=""):
    error_msgs = ''
    result = ''
    try:
        result = invoke_on_host(snippet_list, shell, package)
        result = result[:-1]
    except subprocess.CalledProcessError as error:
        error_msgs = error_msgs + error.stderr
    return result, error_msgs


def get_pkg_attrs(attr_dict, prereqs, package_name=''):
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
                attr_dict['invoke'][step], prereqs)
            if method == 'container':
                # invoke the snippet list in a chroot environment
                result, error_msgs = invoke_in_rootfs_wrapped(
                    snippet_list, prereqs.fs_shell, package=package_name)
            if method == 'host':
                # invoke the snippet list on the host
                result, error_msgs = invoke_on_host_wrapped(
                    snippet_list, prereqs.host_shell, package=package_name)
    if 'delimiter' in attr_dict.keys():
        res_list = result.split(attr_dict['delimiter'])
        if res_list[-1] == '':
            res_list.pop()
            return res_list, error_msgs
        return res_list, error_msgs
    # if there is no delimiter, return the result string
    return result, error_msgs


def get_live_attr_list(attr_dict, prereqs):
    """Similar to get_pkg_attrs in tern/analyze/default/collect.py but with
    invocation on a live container image"""
    error_msgs = ""
    result = ""
    if 'invoke' in attr_dict.keys():
        for step in range(1, len(attr_dict['invoke'].keys()) + 1):
            method, snippet_list = get_snippet_list(
                attr_dict['invoke'][step], prereqs)
            # invoke inventory script against the mount directory
            result, error = lcol.invoke_live(snippet_list, prereqs, method)
            if error:
                logger.warning(
                    "Error invoking command: %s", error.decode('utf-8'))
                error_msgs = error_msgs + error.decode('utf-8')
    if 'delimiter' in attr_dict.keys():
        res_list = result.decode('utf-8').split(attr_dict['delimiter'])
        if res_list[-1] == '' or res_list[-1] == '\n':
            res_list.pop()
            return res_list, error_msgs
        return res_list, error_msgs
    return result, error_msgs


def collect_file_metadata(items):
    """Collect file metadata from the items returned by collecting package
    and file attributes"""
    # convert this data into a list before adding it to the
    # package dictionary
    file_list = []
    for files_str in items:
        # convert the string into a list
        files = []
        for filepath in filter(bool, files_str.split('\n')):
            files.append(filepath.lstrip('/'))
        file_list.append(files)
    return file_list


def collect_list_metadata(listing, prereqs, live=False):
    """Given the listing for the package manager, collect
    metadata that gets returned as a list
    The Prereqs object contains the state of the container filesystem and
    the host."""
    pkg_dict = {}
    msgs = ''
    warnings = ''
    # a valid shell needs to exist in the filesystem for this to work
    for item in command_lib.base_keys:
        # check if the supported items exist in the given listing
        if item in listing.keys():
            if live:
                items, msg = get_live_attr_list(listing[item], prereqs)
            else:
                items, msg = get_pkg_attrs(listing[item], prereqs)
            msgs = msgs + msg
            if item == 'files':
                pkg_dict.update({item: collect_file_metadata(items)})
            else:
                pkg_dict.update({item: items})
        else:
            warnings = warnings + errors.no_listing_for_base_key.format(
                listing_key=item)
    return pkg_dict, msgs, warnings
