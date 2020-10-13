# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to analyze the first layer of a container image in default mode
"""


import logging
import os

from tern.classes.notice import Notice
from tern.command_lib import command_lib
from tern.analyze import common
from tern.report import formats
from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def get_os_release(base_layer):
    '''Given the base layer object, determine if an os-release file exists and
    return the PRETTY_NAME string from it. If no release file exists,
    return an empty string. Assume that the layer filesystem is mounted'''
    # os-release may exist under /etc/ or /usr/lib. We should first check
    # for the preferred /etc/os-release and fall back on /usr/lib/os-release
    # if it does not exist under /etc
    etc_path = os.path.join(
        rootfs.get_untar_dir(base_layer.tar_file), constants.etc_release_path)
    lib_path = os.path.join(
        rootfs.get_untar_dir(base_layer.tar_file), constants.lib_release_path)
    if not os.path.exists(etc_path):
        if not os.path.exists(lib_path):
            return ''
        etc_path = lib_path
    # file exists at this point, try to read it
    with open(etc_path, 'r') as f:
        lines = f.readlines()
    pretty_name = ''
    # iterate through os-release file to find OS
    for line in lines:
        key, val = line.rstrip().split('=', 1)
        if key == "PRETTY_NAME":
            pretty_name = val
            break
    return pretty_name.strip('"')


def get_os_style(image_layer, binary):
    '''Given an ImageLayer object and a binary package manager, check for the
    OS identifier in the os-release file first. If the os-release file
    is not available, make an educated guess as to what kind of OS the layer
    might be based off of given the pkg_format + package manager. If the binary
    provided does not exist in base.yml, add a warning notice'''
    origin_command_lib = formats.invoking_base_commands
    origin_layer = 'Layer {}'.format(image_layer.layer_index)
    pkg_format = command_lib.check_pkg_format(binary)
    os_guess = command_lib.check_os_guess(binary)
    os_release = get_os_release(image_layer)
    if os_release:
        # We know with high degree of certainty what the OS is
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.os_release.format(os_style=os_release), 'info'))
    elif not binary:
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


def execute_base_layer(base_layer, binary, shell):
    '''Execute retrieving base layer packages'''
    try:
        target = rootfs.mount_base_layer(base_layer.tar_file)
        rootfs.prep_rootfs(target)
        common.add_base_packages(base_layer, binary, shell)
    except KeyboardInterrupt:
        logger.critical(errors.keyboard_interrupt)
        abort_analysis()
    finally:
        # unmount proc, sys and dev
        rootfs.undo_mount()
        rootfs.unmount_rootfs()


def analyze_first_layer(image_obj, master_list, redo):
    # set up a notice origin for the first layer
    origin_first_layer = 'Layer {}'.format(image_obj.layers[0].layer_index)
    # check if the layer is empty
    if common.is_empty_layer(image_obj.layers[0]):
        logger.warning(errors.empty_layer)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(errors.empty_layer, 'warning'))
        return ''
    # find the shell from the first layer
    shell = common.get_shell(image_obj.layers[0])
    if not shell:
        logger.warning(errors.no_shell)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(errors.no_shell, 'warning'))
    # find the binary from the first layer
    binary = common.get_base_bin(image_obj.layers[0])
    if not binary:
        logger.warning(errors.no_package_manager)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(errors.no_package_manager, 'warning'))
    # try to load packages from cache
    if not common.load_from_cache(image_obj.layers[0], redo):
        # set a possible OS
        common.get_os_style(image_obj.layers[0], binary)
        # if there is a binary, extract packages
        if shell and binary:
            execute_base_layer(image_obj.layers[0], binary, shell)
    # populate the master list with all packages found in the first layer
    for p in image_obj.layers[0].packages:
        master_list.append(p)
    return shell
