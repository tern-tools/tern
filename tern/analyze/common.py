# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

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
from tern.utils import general
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def get_shell_commands(shell_command_line):
    '''Given a shell command line, get a list of Command objects'''
    comm_list = general.split_command(shell_command_line)
    cleaned_list = []
    for comm in comm_list:
        cleaned_list.append(Command(general.clean_command(comm)))
    return cleaned_list


def load_from_cache(layer, redo=False):
    '''Given a layer object, check against cache to see if that layer id exists
    if yes then get the package list and load it in the layer and return true.
    If it doesn't exist return false. Default operation is to not redo the
    cache. Add notices to the layer's origins matching the origin_str'''
    loaded = False
    if not layer.packages and not redo:
        # there are no packages in this layer and we are not repopulating the
        # cache, try to get it from the cache
        raw_pkg_list = cache.get_packages(layer.fs_hash)
        if raw_pkg_list:
            logger.debug('Loaded from cache: layer \"%s\"', layer.fs_hash[:10])
            for pkg_dict in raw_pkg_list:
                pkg = Package(pkg_dict['name'])
                pkg.fill(pkg_dict)
                layer.add_package(pkg)
            load_notices_from_cache(layer)
            loaded = True
    return loaded


def load_notices_from_cache(layer):
    '''Given a layer object, populate the notices from the cache'''
    origins_list = cache.get_origins(layer.fs_hash)
    for origin_dict in origins_list:
        layer.origins.add_notice_origin(origin_dict['origin_str'])
        for notice in origin_dict['notices']:
            layer.origins.add_notice_to_origins(
                origin_dict['origin_str'], Notice(
                    notice['message'], notice['level']))


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
    cwd = os.path.join(rootfs.get_working_dir(), constants.mergedir)
    for key, value in command_lib.command_lib['base'].items():
        for path in value['path']:
            if os.path.exists(os.path.join(cwd, path)):
                binary = key
                break
    return binary


def get_os_release():
    '''Given the base layer object, determine if an os-release file exists and
    return the PRETTY_NAME string from it. If no release file exists,
    return an empty string. Assume that the layer filesystem is mounted'''
    # os-release may exist under /etc/ or /usr/lib. We should first check
    # for the preferred /etc/os-release and fall back on /usr/lib/os-release
    # if it does not exist under /etc
    etc_path = os.path.join(rootfs.get_working_dir(), constants.mergedir,
                            constants.etc_release_path)
    lib_path = os.path.join(rootfs.get_working_dir(), constants.mergedir,
                            constants.lib_release_path)
    tern_path = command_lib.base_file
    if not os.path.exists(etc_path):
        if not os.path.exists(lib_path):
            if not tern_path:
                return ''
            etc_path = tern_path
        else:
            etc_path = lib_path
    # file exists at this point, try to read it
    with open(etc_path, 'r') as f:
        lines = f.readlines()
    pretty_name = ''
    # iterate through os-release file to find OS
    for l in lines:
        key, val = l.rstrip().split('=', 1)
        if key == "PRETTY_NAME":
            pretty_name = val
            break
    return pretty_name.strip('"')


def collate_list_metadata(shell, listing):
    '''Given the shell and the listing for the package manager, collect
    metadata that gets returned as a list'''
    pkg_dict = {}
    msgs = ''
    warnings = ''
    for item in command_lib.base_keys:
        if item in listing.keys():
            items, msg = command_lib.get_pkg_attr_list(shell, listing[item])
            msgs = msgs + msg
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
               'proj_url': 'proj_urls'}
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
            a_pkg.update({key: value[index]})
        pkg_list.append(a_pkg)
    return pkg_list


def add_base_packages(image_layer, binary, shell):
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
        pkg_dict, invoke_msg, warnings = collate_list_metadata(shell, listing)
        if invoke_msg:
            image_layer.origins.add_notice_to_origins(
                origin_layer, Notice(invoke_msg, 'error'))
        if warnings:
            image_layer.origins.add_notice_to_origins(
                origin_command_lib, Notice(warnings, 'warning'))
        if 'names' in pkg_dict and len(pkg_dict['names']) > 1:
            pkg_list = convert_to_pkg_dicts(pkg_dict)
            for pkg_dict in pkg_list:
                pkg = Package(pkg_dict['name'])
                pkg.fill(pkg_dict)
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
    Fill out: version, license and proj_url
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
    # proj_urls
    url_listing, listing_msg = command_lib.check_library_key(
        pkg_listing, 'proj_url')
    if url_listing:
        url_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, url_listing, package_name=pkg_obj.name)
        if url_list:
            pkg_obj.proj_url = url_list[0]
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


def consolidate_commands(command_list):
    '''Given a list of Command objects, consolidate the install and remove
    commands into one and return a list of resulting command objects'''
    new_list = []
    while command_list:
        first = command_list.pop(0)
        for _ in range(0, len(command_list)):
            second = command_list.pop(0)
            if not first.merge(second):
                command_list.append(first)
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
    command_list = get_shell_commands(shell_command_line)
    for command in command_list:
        command_lib.set_command_attrs(command)
    ignore_msgs, filter1 = remove_ignored_commands(command_list)
    unrec_msgs, filter2 = remove_unrecognized_commands(filter1)
    if ignore_msgs:
        report = report + formats.ignored + ignore_msgs
    if unrec_msgs:
        report = report + formats.unrecognized + unrec_msgs

    return consolidate_commands(filter2), report


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


def get_os_style(image_layer, binary):
    '''Given an ImageLayer object and a binary package manager, check for the
    OS identifier in the os-release file first. If the os-release file
    is not available, make an educated guess as to what kind of OS the layer
    might be based off of given the pkg_format + package manager. If the binary
    provided does not exist in base.yml, add a warning notice'''
    origin_command_lib = formats.invoking_base_commands
    origin_layer = 'Layer: ' + image_layer.fs_hash[:10]
    pkg_format = command_lib.check_pkg_format(binary)
    os_guess = command_lib.check_os_guess(binary)
    if get_os_release():
        # We know with high degree of certainty what the OS is
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.os_release.format(os_style=get_os_release()), 'info'))
    elif binary is None:
        # No binary and no os-release means we have no idea about base OS
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            errors.no_etc_release, 'warning'))
    else:
        # We make a guess about the OS based on pkg_format + binary
        # First check that binary exists in base.yml
        if not pkg_format or not os_guess:
            image_layer.origins.add_notice_to_origins(
                origin_command_lib, Notice(
                    errors.no_listing_for_base_key.format(listing_key=binary),
                    'warning'))
        else:
            # Assign image layer attributes and guess OS
            image_layer.pkg_format = pkg_format
            image_layer.os_guess = os_guess
            image_layer.origins.add_notice_to_origins(origin_layer, Notice(
                formats.os_style_guess.format(
                    package_manager=binary,
                    package_format=image_layer.pkg_format,
                    os_list=image_layer.os_guess), 'info'))
