# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
'''
Common functions
'''

import logging
import os

from tern.classes.package import Package
from tern.classes.notice import Notice
from tern.classes.command import Command
from tern.command_lib import command_lib
from tern.report import formats
from tern.report import errors
from tern.report import content
from tern.utils import cache
from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)


def get_shell_commands(shell_command_line):
    '''Given a shell command line, get a list of Command objects'''
    comm_list = shell_command_line.split('&&')
    cleaned_list = []
    for comm in comm_list:
        cleaned_list.append(Command(comm.strip()))
    return cleaned_list


def load_from_cache(layer, redo=False):
    '''Given a layer object, check against cache to see if that layer id exists
    if yes then get the package list and load it in the layer and return true.
    If it doesn't exist return false. Default operation is to not redo the
    cache. Add notices to the layer's origins matching the origin_str'''
    loaded = False
    origin_layer = 'Layer: ' + layer.fs_hash[:10]
    if not layer.packages and not redo:
        # there are no packages in this layer and we are not repopulating the
        # cache, try to get it from the cache
        raw_pkg_list = cache.get_packages(layer.fs_hash)
        if raw_pkg_list:
            logger.debug('Loaded from cache: layer \"%s\"', layer.fs_hash[:10])
            message = formats.loading_from_cache.format(
                layer_id=layer.fs_hash[:10])
            # add notice to the origin
            layer.origins.add_notice_to_origins(origin_layer, Notice(
                message, 'info'))
            for pkg_dict in raw_pkg_list:
                pkg = Package(pkg_dict['name'])
                pkg.fill(pkg_dict)
                layer.add_package(pkg)
            loaded = True
    return loaded


def save_to_cache(image):
    '''Given an image object, save all layers to the cache'''
    for layer in image.layers:
        if layer.packages:
            cache.add_layer(layer)


def get_base_bin():
    '''Given the base layer object, find the binary used to identify the
    base OS layer. Assume that the layer filesystem is mounted'''
    binary = ''
    # the path to where the filesystem is mounted
    # look at utils/rootfs.py mount_base_layer module
    cwd = os.path.join(os.getcwd(), constants.temp_folder, constants.mergedir)
    for key, value in command_lib.command_lib['base'].items():
        for path in value['path']:
            if os.path.exists(os.path.join(cwd, path)):
                binary = key
                break
    return binary


def add_base_packages(image_layer, binary, shell):  # pylint: disable=too-many-locals
    '''Given the image layer, the binary to invoke and shell:
        1. get the listing from the base.yml
        2. Invoke any commands against the base layer
        3. Make a list of packages and add them to the layer'''
    origin_layer = 'Layer: ' + image_layer.fs_hash[:10]
    if image_layer.created_by:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.layer_created_by.format(created_by=image_layer.created_by),
            'info'))
    else:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.no_created_by, 'warning'))
    origin_command_lib = formats.invoking_base_commands
    # find the binary
    listing = command_lib.get_base_listing(binary)
    if listing:
        # put info notice about what is going to be invoked
        snippet_msg = formats.invoke_for_base + '\n' + \
            content.print_base_invoke(binary)
        image_layer.origins.add_notice_to_origins(
            origin_layer, Notice(snippet_msg, 'info'))
        shell, _ = command_lib.get_image_shell(listing)
        if not shell:
            shell = constants.shell
        # get all the packages in the base layer
        names, n_msg = command_lib.get_pkg_attr_list(shell, listing['names'])
        versions, v_msg = command_lib.get_pkg_attr_list(
            shell, listing['versions'])
        licenses, l_msg = command_lib.get_pkg_attr_list(
            shell, listing['licenses'])
        src_urls, u_msg = command_lib.get_pkg_attr_list(
            shell, listing['src_urls'])
        # add a notice to the image if something went wrong
        invoke_msg = n_msg + v_msg + l_msg + u_msg
        if invoke_msg:
            image_layer.origins.add_notice_to_origins(
                origin_layer, Notice(invoke_msg, 'error'))
        if names and len(names) > 1:
            for index, name in enumerate(names):
                pkg = Package(name)
                if len(versions) == len(names):
                    pkg.version = versions[index]
                if len(licenses) == len(names):
                    pkg.license = licenses[index]
                if len(src_urls) == len(names):
                    pkg.src_url = src_urls[index]
                image_layer.add_package(pkg)
    # if there is no listing add a notice
    else:
        image_layer.origins.add_notice_to_origins(
            origin_command_lib, Notice(errors.no_listing_for_base_key.format(
                listing_key=binary), 'error'))


def fill_package_metadata(pkg_obj, pkg_listing, shell):
    '''Given a Package object and the Package listing from the command
    library, fill in the attribute value returned from looking up the
    data and methods of the package listing.
    Fill out: version, license and src_url
    If there are errors, fill out notices'''
    # create a NoticeOrigin for the package
    origin_str = 'command_lib/snippets.yml'
    # version
    version_listing, listing_msg = command_lib.check_library_key(
        pkg_listing, 'version')
    if version_listing:
        version_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, version_listing, package_name=pkg_obj.name)
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
            shell, license_listing, package_name=pkg_obj.name)
        if license_list:
            pkg_obj.license = license_list[0]
        else:
            pkg_obj.origins.add_notice_to_origins(
                origin_str, Notice(invoke_msg, 'error'))
    else:
        pkg_obj.origins.add_notice_to_origins(
            origin_str, Notice(listing_msg, 'warning'))
    # src_urls
    url_listing, listing_msg = command_lib.check_library_key(
        pkg_listing, 'src_url')
    if url_listing:
        url_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, url_listing, package_name=pkg_obj.name)
        if url_list:
            pkg_obj.src_url = url_list[0]
        else:
            pkg_obj.origins.add_notice_to_origins(
                origin_str, Notice(invoke_msg, 'error'))
    else:
        pkg_obj.origins.add_notice_to_origins(
            origin_str, Notice(listing_msg, 'warning'))


def get_package_dependencies(package_listing, package_name, shell):
    '''The package listing is the result of looking up the command name in the
    command library. Given this listing, the package name and the shell
    return a list of package dependency names'''
    deps_listing, deps_msg = command_lib.check_library_key(
        package_listing, 'deps')
    if deps_listing:
        deps_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, deps_listing, package_name=package_name)
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


def filter_install_commands(shell_command_line):
    '''Given a shell command line:
        1. Create a list of Command objects
        2. For each command, check against the command library for installed
        commands
        3. Return installed command objects, and messages for ignored commands
        and unrecognized commands'''
    report = ''
    command_list = get_shell_commands(shell_command_line)
    for command in command_list:
        command_lib.set_command_attrs(command)
    ignore_msgs, filter1 = remove_ignored_commands(command_list)
    unrec_msgs, filter2 = remove_unrecognized_commands(filter1)
    if ignore_msgs:
        report = report + formats.ignored + ignore_msgs
    if unrec_msgs:
        report = report + formats.unrecognized + unrec_msgs
    return filter2, report


def add_snippet_packages(image_layer, command, pkg_listing, shell):
    '''Given an image layer object, a command object, the package listing
    and the shell used to invoke commands, add package metadata to the layer
    object. We assume the filesystem is already mounted and ready
        1. Get the packages installed by the command
        3. For each package get the dependencies
        4. For each unique package name, find the metadata and add to the
        layer'''
    # set up a notice origin for the layer
    origin_layer = 'Layer: ' + image_layer.fs_hash[:10]
    # find packages for the command
    cmd_msg = formats.invoke_for_snippets + '\n' + \
        content.print_package_invoke(command.name)
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
        fill_package_metadata(pkg, pkg_invoke, shell)
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
