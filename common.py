'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging

from classes.package import Package
from classes.notice import Notice
from classes.command import Command
from command_lib import command_lib
from report import formats
from report import errors
from report import content
from utils import cache
from utils import constants
'''
Common functions
'''

# global logger
logger = logging.getLogger(constants.logger_name)


def get_shell_commands(shell_command_line):
    '''Given a shell command line, get a list of Command objects'''
    comm_list = shell_command_line.split('&&')
    cleaned_list = []
    for comm in comm_list:
        cleaned_list.append(Command(comm.strip()))
    return cleaned_list


def load_from_cache(layer):
    '''Given a layer object, check against cache to see if that layer id exists
    if yes then get the package list and load it in the layer and return true.
    If it doesn't exist return false
    Add notices to the layer's origins matching the origin_str'''
    loaded = False
    origin_str = layer.created_by
    if not layer.packages:
        # there are no packages in this layer
        # try to get it from the cache
        raw_pkg_list = cache.get_packages(layer.diff_id)
        if raw_pkg_list:
            logger.debug('Loaded from cache: layer {}'.format(
                layer.diff_id[:10]))
            message = formats.loading_from_cache.format(
                layer_id=layer.diff_id[:10])
            # add notice to the origin
            layer.origins.add_notice_to_origins(origin_str, Notice(
                message, 'info'))
            for pkg_dict in raw_pkg_list:
                pkg = Package(pkg_dict['name'])
                pkg.fill(pkg_dict)
                layer.add_package(pkg)
            loaded = True
    return loaded


def save_to_cache(image):
    '''Given an image object, check against the cache to see if a layer id
    exists. If no then save the layer and package list to the cache'''
    existing_layers = cache.get_layers()
    for layer in image.layers:
        if layer.diff_id not in existing_layers and layer.packages:
            cache.add_layer(layer)


def get_base_bin(base_layer):
    '''Given the base layer object, find the binary used to identify the
    base OS layer. Assume that the layer filesystem is mounted'''
    binary = ''
    # the path to where the filesystem is mounted
    # look at utils/rootfs.py mount_base_layer module
    cwd = os.path.join(os.getcwd(), constants.temp_folder, constants.mergedir)
    for key in command_lib.command_lib['base'].keys():
        for path in command_lib.command_lib['base'][key]:
            if os.path.exists(os.path.join(cwd, path)):
                binary = key
                break
    return binary


def add_base_packages(base_layer, binary):
    '''Given the base layer and the binary found in layer fs:
        1. get the listing from the base.yml
        2. Invoke any commands against the base layer
        3. Make a list of packages and add them to the layer'''
    origin_layer = base_layer.created_by
    origin_command_lib = 'command_lib/base.yml'
    # find the binary
    listing = command_lib.get_base_listing(binary)
    if listing:
        shell, msg = command_lib.get_image_shell(listing)
        if not shell:
            # add a warning notice for no shell in the command library
            logger.warning('No shell listing in command library. '
                           'Using default shell')
            no_shell_message = errors.no_shell_listing.format(
                binary, default_shell=constants.shell)
            base_layer.origins.add_notice_to_origins(
                origin_command_lib, Notice(no_shell_message, 'warning'))
            # add a hint notice to add the shell to the command library
            add_shell_message = errors.no_listing_for_base_key.format(
                listing_key='shell')
            base_layer.origins.add_notice_origins(
                origin_command_lib, Notice(add_shell_message, 'hint'))
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
            base_layer.origins.add_notice_to_origins(
                origin_layer, Notice(invoke_msg, 'error'))
        if names and len(names) > 1:
            for index in range(0, len(names)):
                pkg = Package(names[index])
                if len(versions) == len(names):
                    pkg.version = versions[index]
                if len(licenses) == len(names):
                    pkg.license = licenses[index]
                if len(src_urls) == len(names):
                    pkg.src_url = src_urls[index]
                base_layer.add_package(pkg)
    # if there is no listing add a notice
    else:
        base_layer.origins.add_notice_to_origins(
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
        else:
            return [], invoke_msg
    else:
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


def add_diff_packages(diff_layer, command_line, shell):
    '''Given a layer object, command line string that created it, and the
    shell used to invoke commands, add package metadata to the layer object
        1. Parse the command line to get individual install commands
        2. For each command get the packages installed
        3. For each package get the dependencies
        4. For each unique package name, find the metadata and add to the
        layer'''
    origin_info = formats.invoke_for_snippets
    diff_layer.origins.add_notice_origin(origin_info)
    # parse all installed commands
    cmd_list, msg = filter_install_commands(command_line)
    if msg:
        diff_layer.origins.add_notice_to_origins(
            origin_info, Notice(msg, 'warning'))
    # find packages for each command
    for command in cmd_list:
        origin_cmd = content.print_package_invoke(command.name)
        diff_layer.origins.add_notice_origin(origin_cmd)
        pkg_list = get_installed_package_names(command)
        # collect all the dependencies for each package name
        all_pkgs = []
        for pkg_name in pkg_list:
            pkg_listing = command_lib.get_package_listing(
                command.name, pkg_name)
            deps, deps_msg = get_package_dependencies(
                pkg_listing, pkg_name, shell)
            if deps_msg:
                logger.warning(deps_msg)
                diff_layer.origins.add_notice_to_origins(origin_info, 'error')
            all_pkgs.append(pkg_name)
            all_pkgs.extend(deps)
        unique_pkgs = list(set(all_pkgs))
        # get package metadata for each package name
        for pkg_name in unique_pkgs:
            pkg = Package(pkg_name)
            pkg_listing = command_lib.get_package_listing(
                command.name, pkg_name)
            fill_package_metadata(pkg, pkg_listing, shell)
            diff_layer.add_package(pkg)
