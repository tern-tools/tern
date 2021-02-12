# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Use an external tool to analyze a container image
"""


import logging
import os
import shutil
from stevedore import driver
from stevedore.exception import NoMatches

from tern.classes.notice import Notice
from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def get_exec_command(command_string):
    '''Given a command as a string, find out if the command exists on the
    system. If it does exist, return a subprocess invokable command list
    where the command is the absolute path of the binary existing on the
    system'''
    cmd_list = command_string.split(' ')
    # we first find if the command exists on the system
    run_bin = cmd_list.pop(0)
    bin_path = shutil.which(run_bin)
    if not bin_path:
        raise OSError("Command {} not found".format(run_bin))
    cmd_list.insert(0, bin_path)
    return cmd_list


def get_filesystem_command(layer_obj, command):
    '''Given an ImageLayer object and a command in the form of a string,
    return the command in list form  with the target directory of the layer.
    This assumes that the layer tarball is untarred, which should have happened
    during the loading of the Image object'''
    # in most cases, the external tool has a CLI where the target directory
    # is the last token in the command. So the most straightforward way
    # to perform this operation is to append the target directory
    cmd_list = get_exec_command(command)
    cmd_list.append(rootfs.get_untar_dir(layer_obj.tar_file))
    return cmd_list


def get_file_command(layer_tar_file, layer_file, command):
    '''Given an ImageLayer object's tar_file property and a FileData object
    from that layer, along with the command, return the command in list form
    with the target file appended at the end'''
    cmd_list = get_exec_command(command)
    file_path = os.path.join(
        rootfs.get_untar_dir(layer_tar_file), layer_file.path)
    cmd_list.append(file_path)
    return cmd_list


def execute_external_command(layer_obj, command, is_sudo=False):
    '''Given an Imagelayer object and a command in the form of a list, execute
    the command and store the results in the ImageLayer object either as
    results or as a Notice object'''
    origin_layer = 'Layer {}'.format(layer_obj.layer_index)
    result, error = rootfs.shell_command(is_sudo, command)
    if error:
        msg = error.decode('utf-8')
        logger.error("Error in executing external command: %s", msg)
        layer_obj.origins.add_notice_to_origins(origin_layer, Notice(
            msg, 'error'))
        return False
    layer_obj.analyzed_output = result.decode('utf-8')
    return True


def execute_and_pass(layer_obj, command, is_sudo=False):
    '''Similar to execute_external_command, but the results and the errors
    are stored together in layer_obj's analyzed_output property to be
    post-processed. The result and error will be separated by two new line
    characters \n\n'''
    full_cmd = get_filesystem_command(layer_obj, command)
    result, error = rootfs.shell_command(is_sudo, full_cmd)
    layer_obj.analyzed_output = error.decode(
        'utf-8') + '\n\n' + result.decode('utf-8')


def run_on_image(image_obj, command, is_sudo=False, redo=False):
    '''Given an Image object, for each layer, run the given command on the
    layer filesystem.
    The layer tarballs should already be extracted (taken care of when
    the Image object is created). The command should already be a completely
    formed string without the target directory.'''

    # check if the command is empty
    if not command:
        logger.error("No command to execute. No report will be generated")
        return False
    # execute for each layer object
    for layer in image_obj.layers:
        # run the command at each layer if we are redoing or if there
        # is nothing in the analyzed output
        if redo or not layer.files_analyzed:
            # set that we're analyzing at the file level
            layer.files_analyzed = True
            # get the actual command
            full_cmd = get_filesystem_command(layer, command)
            if not execute_external_command(layer, full_cmd, is_sudo):
                logger.error(
                    "Error in executing given external command: %s", command)
                return False
    return True


def run_extension(image_obj, ext_string, redo=False):
    '''Depending on what tool the user has chosen to extend with, load that
    extension and run it'''
    try:
        mgr = driver.DriverManager(
            namespace='tern.extensions',
            name=ext_string,
            invoke_on_load=True,
        )
        return mgr.driver.execute(image_obj, redo)
    except NoMatches:
        pass


def run_extension_layer(image_layer, ext_string, redo=False):
    '''Depending on what tool the user has chosen to extend with, load that
    extension and run it'''
    try:
        mgr = driver.DriverManager(
            namespace='tern.extensions',
            name=ext_string,
            invoke_on_load=True,
        )
        return mgr.driver.execute_layer(image_layer, redo)
    except NoMatches:
        pass
