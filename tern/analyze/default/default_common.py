# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Common functions to analyze a container in default mode
"""


import logging
import os
import sys

from tern.classes.notice import Notice
from tern.classes.package import Package
from tern.report import content
from tern.report import formats
from tern.utils import constants
from tern.utils import rootfs
from tern.analyze.default.command_lib import command_lib
from tern.analyze.default import filter

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
    pkg_list = filter.get_installed_package_names(command)
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


def abort_analysis():
    """Abort due to some external event"""
    rootfs.recover()
    sys.exit(1)
