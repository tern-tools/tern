# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Common functions to analyze a container in default mode
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


def get_shell(layer):
    '''Find the shell if any on the layer filesystem. Assume that the layer
    has already been unpacked. If there is no shell, return an empty string'''
    shell = ''
    cwd = rootfs.get_untar_dir(layer.tar_file)
    for sh in command_lib.command_lib['common']['shells']:
        realpath = os.path.realpath(os.path.join(cwd, sh[1:]))
        # If realpath is a symlink and points to the root of the container,
        # check for existence of the linked binary in current working dir
        if realpath[0] == '/' and os.path.exists(os.path.join(cwd,
                                                              realpath[1:])):
            return sh
        # otherwise, just follow symlink in same folder and
        # remove leading forwardslash before joining paths
        if os.path.exists(os.path.join(cwd, sh[1:])):
            return sh
    return shell


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


def fill_package_metadata(pkg_obj, pkg_listing, shell, work_dir, envs):
    '''Given a Package object and the Package listing from the command
    library, fill in the attribute value returned from looking up the
    data and methods of the package listing.
    Fill out: version, license and proj_url
    If there are errors, fill out notices'''
    # create a NoticeOrigin for the package
    origin_str = 'command_lib/snippets.yml'
    # version
    version_listing, listing_msg = command_lib.check_library_key(
        pkg_listing, 'version')
    if version_listing:
        version_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, version_listing, work_dir, envs, package_name=pkg_obj.name)
        if version_list:
            pkg_obj.version = version_list[0]
        else:
            pkg_obj.origins.add_notice_to_origins(
                origin_str, Notice(invoke_msg, 'error'))
    else:
        pkg_obj.origins.add_notice_to_origins(
            origin_str, Notice(listing_msg, 'warning'))
    # license
    license_listing, listing_msg = command_lib.check_library_key(
        pkg_listing, 'license')
    if license_listing:
        license_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, license_listing, work_dir, envs, package_name=pkg_obj.name)
        if license_list:
            pkg_obj.license = license_list[0]
        else:
            pkg_obj.origins.add_notice_to_origins(
                origin_str, Notice(invoke_msg, 'error'))
    else:
        pkg_obj.origins.add_notice_to_origins(
            origin_str, Notice(listing_msg, 'warning'))
    # proj_urls
    url_listing, listing_msg = command_lib.check_library_key(
        pkg_listing, 'proj_url')
    if url_listing:
        url_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, url_listing, work_dir, envs, package_name=pkg_obj.name)
        if url_list:
            pkg_obj.proj_url = url_list[0]
        else:
            pkg_obj.origins.add_notice_to_origins(
                origin_str, Notice(invoke_msg, 'error'))
    else:
        pkg_obj.origins.add_notice_to_origins(
            origin_str, Notice(listing_msg, 'warning'))


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
    command_list, branch_report = get_shell_commands(shell_command_line)
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


def add_snippet_packages(image_layer, command, pkg_listing, shell, work_dir,  # pylint:disable=too-many-arguments,too-many-locals
                         envs):
    '''Given an image layer object, a command object, the package listing
    and the shell used to invoke commands, add package metadata to the layer
    object. We assume the filesystem is already mounted and ready
        1. Get the packages installed by the command
        3. For each package get the dependencies
        4. For each unique package name, find the metadata and add to the
        layer'''
    # set up a notice origin for the layer
    origin_layer = 'Layer {}'.format(image_layer.layer_index)
    # find packages for the command
    cmd_msg = (formats.invoke_for_snippets + '\n' +
               content.print_package_invoke(command.name))
    image_layer.origins.add_notice_to_origins(origin_layer, Notice(
        cmd_msg, 'info'))
    pkg_list = get_installed_package_names(command)
    # collect all the dependencies for each package name
    all_pkgs = []
    for pkg_name in pkg_list:
        pkg_invoke = command_lib.check_for_unique_package(
            pkg_listing, pkg_name)
        deps, deps_msg = get_package_dependencies(
            pkg_invoke, pkg_name, shell)
        if deps_msg:
            logger.warning(deps_msg)
            image_layer.origins.add_notice_to_origins(
                origin_layer, Notice(deps_msg, 'error'))
        all_pkgs.append(pkg_name)
        all_pkgs.extend(deps)
    unique_pkgs = list(set(all_pkgs))
    # get package metadata for each package name
    for pkg_name in unique_pkgs:
        pkg = Package(pkg_name)
        fill_package_metadata(pkg, pkg_invoke, shell, work_dir, envs)
        image_layer.add_package(pkg)


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
