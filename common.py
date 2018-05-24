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
from utils.container import check_container
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


def load_from_cache(image):
    '''Given an image object, check against cache to see if a layer id exists
    if yes then get the package list and load it in the image layer. If it
    doesn't exist continue. If not all the layers have packages, return False
    else return True'''
    is_full = True
    # check if we can use repotag
    origin_str = ''
    if image.repotag:
        origin_str = image.repotag
    else:
        origin_str = 'Image ID - ' + image.id[:10]
    for layer in image.layers:
        if not layer.packages:
            # create an origin for this layer
            origin_str = origin_str + ': ' + layer.diff_id[:10]
            # there are no packages in this layer
            # try to get it from the cache
            raw_pkg_list = cache.get_packages(layer.diff_id)
            if not raw_pkg_list:
                is_full = False
            else:
                logger.debug('Loaded from cache: layer {}'.format(
                    layer.diff_id[:10]))
                message = formats.loading_from_cache.format(
                    layer_id=layer.diff_id[:10])
                # add notice to the origin
                layer.origins.add_notice_to_origins(
                    origin_str, Notice(message, 'info'))
                for pkg_dict in raw_pkg_list:
                    pkg = Package(pkg_dict['name'])
                    pkg.fill(pkg_dict)
                    layer.add_package(pkg)
    return is_full


def save_to_cache(image):
    '''Given an image object, check against the cache to see if a layer id
    exists. If no then save the layer and package list to the cache'''
    existing_layers = cache.get_layers()
    for layer in image.layers:
        if layer.diff_id not in existing_layers and layer.packages:
            cache.add_layer(layer)


def add_base_packages(image):
    '''Given an image object, get a list of package objects from
    invoking the commands in the command library base section:
        1. For the image and tag name find if there is a list of package names
        2. If there is an invoke dictionary, invoke the commands
        3. Create a list of packages
        4. Add them to the image'''
    # information under the base image tag in the command library
    listing = command_lib.get_base_listing(image.name, image.tag)
    # create the origin for the base image
    origin_info = formats.invoking_base_commands + '\n' + \
        content.print_base_invoke(image.name, image.tag)
    image.origins.add_notice_origin(origin_info)
    origin_str = 'command_lib/base.yml'
    if listing:
        shell, msg = command_lib.get_image_shell(listing)
        if not shell:
            # add a warning notice for no shell in the command library
            logger.warning('No shell listing in command library. '
                           'Using default shell')
            no_shell_message = errors.no_shell_listing.format(
                image_name=image.name, image_tag=image.tag,
                default_shell=constants.shell)
            image.origins.add_notice_to_origins(
                origin_str, Notice(no_shell_message, 'warning'))
            # add a hint notice to add the shell to the command library
            add_shell_message = errors.no_listing_for_base_key.format(
                listing_key='shell')
            image.origins.add_notice_origins(
                origin_str, Notice(add_shell_message, 'hint'))
            shell = constants.shell
        # check if a container is running first
        # eventually this needs to change to use derivatives that have
        # more than 1 layer
        # for now, we add the list of packages to all the layers in a
        # starting base image
        if check_container():
            names, n_msg = command_lib.get_pkg_attr_list(
                shell, listing['names'], chroot=False)
            versions, v_msg = command_lib.get_pkg_attr_list(
                shell, listing['versions'], chroot=False)
            licenses, l_msg = command_lib.get_pkg_attr_list(
                shell, listing['licenses'], chroot=False)
            src_urls, u_msg = command_lib.get_pkg_attr_list(
                shell, listing['src_urls'], chroot=False)
            # add a notice to the image if something went wrong
            invoke_msg = n_msg + v_msg + l_msg + u_msg
            if invoke_msg:
                image.origins.add_notice_to_origins(
                    origin_str, Notice(invoke_msg, 'error'))
            if names and len(names) > 1:
                for index in range(0, len(names)):
                    pkg = Package(names[index])
                    if len(versions) == len(names):
                        pkg.version = versions[index]
                    if len(licenses) == len(names):
                        pkg.license = licenses[index]
                    if len(src_urls) == len(names):
                        pkg.src_url = src_urls[index]
                        for layer in image.layers:
                            layer.add_package(pkg)
        # if no container is running give a logging error
        else:
            logger.error(errors.no_running_docker_container)
    # if there is no listing add a notice
    else:
        image.origins.add_notice_to_origins(
            origin_str, Notice(errors.no_image_tag_listing.format(
                image_name=image.name, image_tag=image.tag), 'error'))


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
            shell, version_listing, package_name=pkg_obj.name, chroot=False)
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
            shell, license_listing, package_name=pkg_obj.name, chroot=False)
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
        pkg_listing, 'license')
    if url_listing:
        url_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, url_listing, package_name=pkg_obj.name, chroot=False)
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
    deps_listing, deps_msg = command_lib.check_library_key(package_listing, 'deps')
    if deps_listing:
        deps_list, invoke_msg = command_lib.get_pkg_attr_list(
            shell, deps_listing, package_name=package_name, chroot=False)
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
