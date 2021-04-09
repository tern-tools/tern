# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to analyze the first layer of a container image in default mode
"""


import logging
import os
import subprocess  # nosec

from tern.classes.notice import Notice
from tern.analyze.default.command_lib import command_lib
from tern.report import formats
from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs
from tern.utils import host
from tern.analyze import common as com
from tern.analyze.default import default_common as dcom
from tern.analyze.default import core

# global logger
logger = logging.getLogger(constants.logger_name)


def find_os_release(host_path):
    """Find the OS PRETTY_NAME in the given path. If no os-release file
    exists, return an empty string"""
    # os-release may exist under /etc/ or /usr/lib. We should first check
    # for the preferred /etc/os-release and fall back on /usr/lib/os-release
    # if it does not exist under /etc
    etc_path = os.path.join(host_path, constants.etc_release_path)
    lib_path = os.path.join(host_path, constants.lib_release_path)
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


def get_os_release(base_layer):
    """Assuming that the layer tarball is untarred are ready to be inspected,
    get the OS information from the os-release file"""
    return find_os_release(rootfs.get_untar_dir(base_layer.tar_file))


def get_os_style(image_layer, binary):
    '''Given an ImageLayer object and a binary package manager, check for the
    OS identifier in the os-release file first. If the os-release file
    is not available, make an educated guess as to what kind of OS the layer
    might be based off of given the pkg_format + package manager. If the binary
    provided does not exist in base.yml, add a warning notice'''
    origin_layer = 'Layer {}'.format(image_layer.layer_index)
    # see if we can find what OS this is
    os_release = get_os_release(image_layer)
    if os_release:
        # We know with high degree of certainty what the OS is
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.os_release.format(os_style=os_release), 'info'))
        # we can set the OS of the image layer
        image_layer.os_guess = os_release
    else:
        # We will try looking for the possible OSs based on the binary
        os_guess = command_lib.check_os_guess(binary)
        if os_guess:
            # We can make a guess
            image_layer.origins.add_notice_to_origins(origin_layer, Notice(
                formats.os_style_guess.format(
                    package_manager=binary, os_list=os_guess), 'info'))
            image_layer.os_guess = os_guess
        else:
            # No binary and no os-release means we have no idea about base OS
            image_layer.origins.add_notice_to_origins(origin_layer, Notice(
                errors.no_etc_release, 'warning'))

    # set a package format if there is one for this binary
    image_layer.pkg_format = command_lib.check_pkg_format(binary)


def mount_first_layer(layer_obj):
    try:
        target = rootfs.mount_base_layer(layer_obj.tar_file)
        rootfs.prep_rootfs(target)
        return target
    except subprocess.CalledProcessError as e:  # nosec
        logger.critical("Cannot mount filesystem and/or device nodes: %s", e)
        dcom.abort_analysis()
    except KeyboardInterrupt:
        logger.critical(errors.keyboard_interrupt)
        dcom.abort_analysis()


def analyze_first_layer(image_obj, master_list, options):
    """Analyze the first layer of an image. Return a Prereqs object for the
    next layer.
    1. Check if the layer is empty. If it is not, return None
    2. See if we can load the layer from cache
    3. If we can't load from cache
    3.1 See if we can find any information about the rootfs
    3.2 If we are able to find any information, use any prescribed methods
        to extract package information
    4. Process and bundle that information into the image object
    5. Return a Prereqs object for subsequent layer processing"""
    # set up a notice origin for the first layer
    origin_first_layer = 'Layer {}'.format(image_obj.layers[0].layer_index)
    # check if the layer is empty
    if com.is_empty_layer(image_obj.layers[0]):
        logger.warning(errors.empty_layer)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(errors.empty_layer, 'warning'))
        return None
    # create a Prereqs object
    prereqs = core.Prereqs()
    # find the shell from the first layer
    prereqs.fs_shell = dcom.get_shell(image_obj.layers[0])
    # find a shell for the host
    prereqs.host_shell = host.check_shell()
    if not prereqs.fs_shell and not prereqs.host_shell:
        logger.warning(errors.no_shell)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(errors.no_shell, 'warning'))
    # find the binary from the first layer
    prereqs.binary = dcom.get_base_bin(image_obj.layers[0])
    # try to load packages from cache
    if not com.load_from_cache(image_obj.layers[0], options.redo):
        # add a notice if there is a "created by"
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(formats.layer_created_by.format(
                created_by=image_obj.layers[0].created_by), 'info'))
        # set a possible OS and package format
        get_os_style(image_obj.layers[0], prereqs.binary)
        # if there is a binary, extract packages
        if prereqs.binary:
            # mount the first layer
            target_dir = mount_first_layer(image_obj.layers[0])
            # set the host path to the mount point
            prereqs.host_path = target_dir
            # core default execution on the first layer
            core.execute_base(image_obj.layers[0], prereqs)
            # unmount
            rootfs.undo_mount()
            rootfs.unmount_rootfs()
        else:
            logger.warning(errors.no_package_manager)
            image_obj.layers[0].origins.add_notice_to_origins(
                origin_first_layer, Notice(
                    errors.no_package_manager, 'warning'))
            return None
    # populate the master list with all packages found in the first layer
    for p in image_obj.layers[0].packages:
        master_list.append(p)
    return prereqs
