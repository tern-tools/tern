# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Analyze a Docker container image
"""

import logging
import sys

from tern.report import errors
from tern.report import formats
from tern.utils import constants
from tern.utils import rootfs
from tern.classes.notice import Notice
from tern.analyze import common
import tern.analyze.docker.helpers as dhelper
from tern.command_lib import command_lib
from tern.analyze.docker import dockerfile as d_file


# global logger
logger = logging.getLogger(constants.logger_name)


def analyze_docker_image(image_obj, redo=False, dockerfile=False, dfobj=None):
    '''Given a DockerImage object, for each layer, retrieve the packages, first
    looking up in cache and if not there then looking up in the command
    library. For looking up in command library first mount the filesystem
    and then look up the command library for commands to run in chroot.
    If there's a dockerfile object available, extract any package
    information from the layers.'''

    # set up empty master list of packages
    master_list = []
    prepare_for_analysis(image_obj, dockerfile)
    # Analyze the first layer and get the shell
    shell = analyze_first_layer(image_obj, master_list, redo)
    # Analyze the remaining layers
    analyze_subsequent_layers(image_obj, shell, master_list, redo, dfobj)
    common.save_to_cache(image_obj)


def get_shell(image_obj, binary):
    # set up a notice origin referring to the base command library listing
    origin_command_lib = formats.invoking_base_commands
    # find the shell to invoke commands in
    shell, _ = command_lib.get_image_shell(
        command_lib.get_base_listing(binary))
    if not shell:
        # add a warning notice for no shell in the command library
        logger.warning('No shell listing in command library. '
                       'Using default shell')
        no_shell_message = errors.no_shell_listing.format(
            binary=binary, default_shell=constants.shell)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_command_lib, Notice(no_shell_message, 'warning'))
        # add a hint notice to add the shell to the command library
        add_shell_message = errors.no_listing_for_base_key.format(
            listing_key='shell')
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_command_lib, Notice(add_shell_message, 'hint'))
        shell = constants.shell
    return shell


def prepare_for_analysis(image_obj, dockerfile):
    # find the layers that are imported
    if dockerfile:
        dhelper.set_imported_layers(image_obj)
    # add notices for each layer if it is imported
    image_setup(image_obj)
    # set up the mount points
    rootfs.set_up()


def abort_analysis():
    '''Abort due to some external event'''
    rootfs.recover()
    sys.exit(1)


def analyze_first_layer(image_obj, master_list, redo):
    # find the binary of the first layer
    binary = common.get_base_bin(image_obj.layers[0])
    # see if there is an associated shell
    # if there is no binary, this will be set to the default shell
    shell = get_shell(image_obj, binary)
    # set a possible OS
    image_obj.layers[0].os_guess = common.get_os_release()
    # set up a notice origin for the first layer
    origin_first_layer = 'Layer: ' + image_obj.layers[0].fs_hash[:10]
    # try to load packages from cache
    loaded = common.load_from_cache(image_obj.layers[0], redo)
    # if there is a binary, we can set other things
    if binary:
        # Determine package/os style from binary in the image layer
        common.get_os_style(image_obj.layers[0], binary)
        # Update os_guess to default if /etc/os-release not available
        if not image_obj.layers[0].os_guess:
            image_obj.layers[0].os_guess = command_lib.check_os_guess(binary)
        # if no packages are loaded from the cache, we can try to extract it
        if not loaded:
            try:
                target = rootfs.mount_base_layer(image_obj.layers[0].tar_file)
                rootfs.prep_rootfs(target)
                common.add_base_packages(image_obj.layers[0], binary, shell)
                # unmount proc, sys and dev
                rootfs.undo_mount()
                rootfs.unmount_rootfs()
            except KeyboardInterrupt:
                logger.critical(errors.keyboard_interrupt)
                abort_analysis()
    else:
        logger.warning(errors.no_package_manager)
        # /etc/os-release may still be present even if binary is not
        common.get_os_style(image_obj.layers[0], None)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(errors.no_package_manager, 'warning'))
    # populate the master list with all packages found in the first layer
    for p in image_obj.layers[0].packages:
        master_list.append(p)
    return shell


def analyze_subsequent_layers(image_obj, shell, master_list, redo, dfobj=None):  # pylint:disable=too-many-branches
    # get packages for subsequent layers
    curr_layer = 1
    while curr_layer < len(image_obj.layers):  # pylint:disable=too-many-nested-blocks
        if not common.load_from_cache(image_obj.layers[curr_layer], redo):
            # get commands that created the layer
            # for docker images this is retrieved from the image history
            command_list = dhelper.get_commands_from_history(
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
                # pin any installed packages to a locked dockerfile.
                if dfobj is not None:
                    # collect list of RUN commands that could install pkgs
                    run_dict = d_file.get_run_layers(dfobj)
                    for package in image_obj.layers[curr_layer].packages:
                        # check that package is in current dfobj RUN line
                        if d_file.package_in_dockerfile(
                                run_dict[curr_layer - 1], package.name):
                            d_file.expand_package(
                                run_dict[curr_layer - 1], package.name,
                                package.version,
                                command_lib.check_pinning_separator(
                                    pkg_listing))
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
        if layer.import_str:
            layer.origins.add_notice_to_origins(origin_str, Notice(
                'Imported in Dockerfile using: ' + layer.import_str, 'info'))


def mount_overlay_fs(image_obj, top_layer):
    '''Given the image object and the top most layer, mount all the layers
    until the top layer using overlayfs'''
    tar_layers = []
    for index in range(0, top_layer + 1):
        tar_layers.append(image_obj.layers[index].tar_file)
    target = rootfs.mount_diff_layers(tar_layers)
    return target
