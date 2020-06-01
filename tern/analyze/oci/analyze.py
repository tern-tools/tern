# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Analyze a OCI format image
"""

import sys
import logging
from tern.utils import rootfs
from tern.report import errors
from tern.analyze import common
from tern.utils import constants
from tern.analyze.oci import helpers
from tern.classes.notice import Notice
from tern.command_lib import command_lib


# global logger
logger = logging.getLogger(constants.logger_name)


def analyze_oci_image(image_obj, redo=False):
    '''Given a OCIImage object, for each layer, retrieve the packages, first
    looking up in cache and if not there then looking up in the command
    library. For looking up in command library first mount the filesystem
    and then look up the command library for commands to run in chroot.'''

    # set up empty master list of packages
    master_list = []
    prepare_for_analysis(image_obj)
    # Analyze the first layer and get the shell
    shell = analyze_first_layer(image_obj, master_list, redo)
    # Analyze the remaining layers
    analyze_subsequent_layers(image_obj, shell, master_list, redo)
    common.save_to_cache(image_obj)


def prepare_for_analysis(image_obj):
    # add notices for each layer if it is imported
    image_setup(image_obj)
    # set up the mount points
    rootfs.set_up()


def abort_analysis():
    '''Abort due to some external event'''
    rootfs.recover()
    sys.exit(1)


def analyze_first_layer(image_obj, master_list, redo):
    # set up a notice origin for the first layer
    origin_first_layer = 'Layer: ' + image_obj.layers[0].fs_hash[:10]
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


def analyze_subsequent_layers(image_obj, shell, master_list, redo):  # noqa: R0912,R0913
    # get packages for subsequent layers
    curr_layer = 1
    # pylint:disable=too-many-nested-blocks
    while curr_layer < len(image_obj.layers):
        # if there is no shell, try to see if it exists in the current layer
        if not shell:
            shell = common.get_shell(image_obj.layers[curr_layer])
        if not common.load_from_cache(image_obj.layers[curr_layer], redo):
            # get commands that created the layer
            # for docker images this is retrieved from the image history
            command_list = helpers.get_commands_from_history(
                image_obj.layers[curr_layer])
            if command_list:
                # mount diff layers from 0 till the current layer
                target = mount_overlay_fs(image_obj, curr_layer)
                # mount dev, sys and proc after mounting diff layers
                rootfs.prep_rootfs(target)
            # for each command look up the snippet library
            for command in command_list:
                pkg_listing = command_lib.get_package_listing(command.name)
                if isinstance(pkg_listing, str):
                    try:
                        common.add_base_packages(
                            image_obj.layers[curr_layer], pkg_listing, shell)
                    except KeyboardInterrupt:
                        logger.critical(errors.keyboard_interrupt)
                        abort_analysis()
                else:
                    try:
                        common.add_snippet_packages(
                            image_obj.layers[curr_layer], command, pkg_listing,
                            shell)
                    except KeyboardInterrupt:
                        logger.critical(errors.keyboard_interrupt)
                        abort_analysis()
            if command_list:
                rootfs.undo_mount()
                rootfs.unmount_rootfs()
        # update the master list
        common.update_master_list(master_list, image_obj.layers[curr_layer])
        curr_layer = curr_layer + 1


def image_setup(image_obj):
    '''Add notices for each layer'''
    for layer in image_obj.layers:
        origin_str = 'Layer: ' + layer.fs_hash[:10]
        layer.origins.add_notice_origin(origin_str)


def mount_overlay_fs(image_obj, top_layer):
    '''Given the image object and the top most layer, mount all the layers
    until the top layer using overlayfs'''
    tar_layers = []
    for index in range(0, top_layer + 1):
        tar_layers.append(image_obj.layers[index].tar_file)
    target = rootfs.mount_diff_layers(tar_layers)
    return target
