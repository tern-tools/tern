# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to process data returned from invoking retrieval commands
"""


import logging
import os

from tern.classes.notice import Notice
from tern.classes.file_data import FileData
from tern.classes.package import Package
from tern.command_lib import command_lib
from tern.report import content
from tern.report import formats
from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def get_pkg_attr_list(shell, attr_dict, work_dir, envs, package_name=''):
    '''The command library has package attributes listed like this:
        {invoke: {1: {container: [command1, command2]},
                  2: {host: [command1, command2]}}, delimiter: <delimiter}
    Given the shell to use, the attribute dictionary and the package name, get
    the result of the invokes, apply the delimiter to create a list and
    return the list.
    chroot is used to indicate whether to run the commands in a chroot
    environment and defaults to True
    override is used for an alternate container name and defaults to
    an empty string'''
    attr_list = []
    error_msgs = ''
    if 'invoke' in attr_dict.keys():
        # invoke the commands
        for step in range(1, len(attr_dict['invoke'].keys()) + 1):
            if 'container' in attr_dict['invoke'][step].keys():
                snippet_list = attr_dict['invoke'][step]['container']
                result = ''
                # If environment variables exist, set them
                if envs:
                    for var in envs:
                        snippet_list.insert(0, 'export ' + var.split('=')[0] +
                                            '=' + var.split('=')[1])
                # If work_dir exist cd into it
                if work_dir is not None:
                    snippet_list.insert(0, 'cd ' + work_dir)
                # if we need to run in a chroot environment
                try:
                    result = invoke_in_rootfs(
                        snippet_list, shell, package=package_name)
                except subprocess.CalledProcessError as error:
                    error_msgs = error_msgs + error.output
                result = result[:-1]
                if 'delimiter' in attr_dict.keys():
                    res_list = result.split(attr_dict['delimiter'])
                    if res_list[-1] == '':
                        res_list.pop()
                    attr_list.extend(res_list)
                else:
                    attr_list.append(result)
    return attr_list, error_msgs


def collate_list_metadata(shell, listing, work_dir, envs):
    '''Given the shell and the listing for the package manager, collect
    metadata that gets returned as a list'''
    pkg_dict = {}
    msgs = ''
    warnings = ''
    if not shell:
        msgs = "Cannot invoke commands without a shell\n"
        return pkg_dict, msgs, warnings
    for item in command_lib.base_keys:
        if item in listing.keys():
            items, msg = command_lib.get_pkg_attr_list(shell, listing[item],
                                                       work_dir, envs)
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


def convert_to_pkg_dicts(pkg_dict):
    '''The pkg_dict is what gets returned after collecting individual
    metadata as a list. It looks like this if property collected:
        {'names': [....], 'versions': [...], 'licenses': [...], ....}
    Convert these into a package dictionary expected by the Package
    Object'''
    mapping = {'name': 'names',
               'version': 'versions',
               'pkg_license': 'licenses',
               'copyright': 'copyrights',
               'proj_url': 'proj_urls',
               'pkg_licenses': 'pkg_licenses',
               'files': 'files'}
    pkg_list = []
    len_names = len(pkg_dict['names'])
    # make a list of keys that correspond with package property names
    new_dict = {}
    for key, value in mapping.items():
        if value in pkg_dict.keys():
            if len(pkg_dict[value]) == len_names:
                new_dict.update({key: pkg_dict[value]})
            else:
                logger.warning("Inconsistent lengths for key: %s", value)
    # convert each of the keys into package dictionaries
    for index, _ in enumerate(new_dict['name']):
        a_pkg = {}
        for key, value in new_dict.items():
            if key == 'files':
                # update the list with FileData objects in dictionary format
                fd_list = []
                for filepath in value[index]:
                    fd_dict = FileData(
                        os.path.split(filepath)[1], filepath).to_dict()
                    fd_list.append(fd_dict)
                a_pkg.update({'files': fd_list})
            else:
                a_pkg.update({key: value[index]})
        pkg_list.append(a_pkg)
    return pkg_list
