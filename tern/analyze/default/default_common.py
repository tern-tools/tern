# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Common functions to analyze a container in default mode
"""


import logging
import os
import sys

from tern.classes.notice import Notice
from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs
from tern.utils import general
from tern.analyze.default.command_lib import command_lib
from tern.analyze.default import filter as fltr

# global logger
logger = logging.getLogger(constants.logger_name)


def find_shell(fspath):
    """Given the path to the filesystem where a shell may exist, find the
    first available shell"""
    for sh in command_lib.command_lib['common']['shells']:
        realpath = os.path.realpath(os.path.join(fspath, sh[1:]))
        # If realpath is a symlink and points to the root of the container,
        # check for existence of the linked binary in current working dir
        if realpath[0] == '/' and os.path.exists(os.path.join(fspath,
                                                              realpath[1:])):
            return sh
        # otherwise, just follow symlink in same folder and
        # remove leading forwardslash before joining paths
        if os.path.exists(os.path.join(fspath, sh[1:])):
            return sh
    return ''


def get_shell(layer):
    '''Find the shell if any on the layer filesystem. Assume that the layer
    has already been unpacked. If there is no shell, return an empty string'''
    cwd = rootfs.get_untar_dir(layer.tar_file)
    return find_shell(cwd)


def get_base_bin(first_layer):
    '''Find the binary used to identify the base OS for the container image.
    We do this by providing the path to the first layer of the container
    image and looking for known binaries there. Assume that the layer has
    already been unpacked with the filesystem'''
    binary = ''
    cwd = rootfs.get_untar_dir(first_layer.tar_file)
    for key, value in command_lib.command_lib['base'].items():
        for path in value['path']:
            if os.path.exists(os.path.join(cwd, path)):
                binary = key
                break
    return binary


def get_existing_bins(fspath):
    """Return a list of all the binaries existing on the given filesystem"""
    bin_list = []
    for key, value in command_lib.command_lib['base'].items():
        for path in value['path']:
            if os.path.exists(os.path.join(fspath, path)):
                bin_list.append(key)
    return bin_list


def fill_package_metadata(pkg_obj, pkg_listing, shell, work_dir, envs):
    '''Given a Package object and the Package listing from the command
    library, fill in the attribute value returned from looking up the
    data and methods of the package listing.If there are errors, fill out
    notices'''
    # create a NoticeOrigin for the package
    origin_str = 'command_lib/snippets.yml'
    pkg_dict = {}
    for key in command_lib.package_keys:
        key_listing, listing_msg = command_lib.check_library_key(
            pkg_listing, key)
        if key_listing:
            key_list, invoke_msg = command_lib.get_pkg_attr_list(
                shell, key_listing, work_dir, envs, package_name=pkg_obj.name)
            if key_list:
                pkg_dict.update({key: key_list})
            else:
                pkg_obj.origins.add_notice_to_origins(
                    origin_str, Notice(invoke_msg, 'error'))
        else:
            pkg_obj.origins.add_notice_to_origins(
                origin_str, Notice(listing_msg, 'warning'))
    pkg_obj.fill(pkg_dict)


def get_package_dependencies(package_listing, package_name, shell,
                             work_dir=None, envs=None):
    '''The package listing is the result of looking up the command name in the
    command library. Given this listing, the package name and the shell
    return a list of package dependency names'''
    deps_listing, deps_msg = command_lib.check_library_key(
        package_listing, 'deps')
    if deps_listing:
        deps_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, deps_listing, work_dir, envs, package_name=package_name)
        if deps_list:
            return list(set(deps_list)), ''
        return [], invoke_msg
    return [], deps_msg


def get_commands_from_metadata(image_layer):
    """Given the image layer object, get the list of command objects that
    created the layer. Return an empty list of we can't do that"""
    # set up notice origin for the layer
    origin_layer = 'Layer {}'.format(image_layer.layer_index)
    # check if there is a key containing the script that created the layer
    if image_layer.created_by:
        cmd, instr = fltr.get_run_command(image_layer.created_by)
        if image_layer.layer_index != 1 and instr in ['ADD', 'COPY']:
            # add a notice saying we cannot analyze files
            # imported from the host during container build
            image_layer.origins.add_notice_to_origins(
                origin_layer, Notice(errors.no_able_to_analyze, 'warning'))
            return []
        if cmd:
            command_list, msg = fltr.filter_install_commands(
                general.clean_command(cmd))
            if msg:
                image_layer.origins.add_notice_to_origins(
                    origin_layer, Notice(msg, 'warning'))
            return command_list
    image_layer.origins.add_notice_to_origins(
        origin_layer, Notice(errors.no_created_by, 'warning'))
    return []


def update_master_list(master_list, layer_obj):
    '''Given a master list of package objects and a layer object containing a
    list of package objects, append to the master list all the package objects
    that are not in the master list and remove the duplicate packages from the
    layer object'''
    # temporary placement of package objects
    unique = []
    for _ in range(len(layer_obj.packages)):
        item = layer_obj.packages.pop(0)
        # check for whether the package exists on the master list
        exists = False
        for pkg in master_list:
            if item.is_equal(pkg):
                exists = True
                break
        if not exists:
            unique.append(item)
    # add all the unique packages to the master list
    for u in unique:
        master_list.append(u)
    # empty the unique packages back into the layer object
    while unique:
        layer_obj.packages.append(unique.pop(0))
    del unique


def abort_analysis():
    """Abort due to some external event"""
    rootfs.recover()
    sys.exit(1)
