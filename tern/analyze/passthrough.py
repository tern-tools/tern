# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Use an external tool to analyze a container image
"""


import logging
from stevedore import driver
from stevedore.exception import NoMatches

from tern.classes.notice import Notice
from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def get_filesystem_command(layer_obj, command):
    '''Given an ImageLayer object and a command in the form of a string,
    return the command in list form  with the target directory of the layer.
    This assumes that the layer tarball is untarred, which should have happened
    during the loading of the Image object'''
    cmd_list = command.split(' ')
    # in most cases, the external tool has a CLI where the target directory
    # is the last token in the command. So the most straightforward way
    # to perform this operation is to append the target directory
    cmd_list.append(rootfs.get_untar_dir(layer_obj.tar_file))
    return cmd_list


def execute_external_command(layer_obj, command):
    '''Given an Imagelayer object and a command in the form of a list, execute
    the command and store the results in the ImageLayer object either as
    results or as a Notice object'''
    origin_layer = 'Layer: ' + layer_obj.fs_hash[:10]
    result, error = rootfs.shell_command(command)
    if error:
        logger.error("Error in executing external command: %s", str(error))
        layer_obj.origins.add_notice_to_origins(origin_layer, Notice(
            str(error), 'error'))
        return False
    layer_obj.analyzed_output = result.decode()
    return True


def run_on_image(image_obj, command):
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
        # set that we're analyzing at the file level
        layer.files_analyzed = True
        # get the actual command
        full_cmd = get_filesystem_command(layer, command)
        if not execute_external_command(layer, full_cmd):
            logger.error(
                "Error in executing given external command: %s", command)
            return False
    return True


def run_extension(image_obj, ext_string):
    '''Depending on what tool the user has chosen to extend with, load that
    extension and run it'''
    try:
        mgr = driver.DriverManager(
            namespace='tern.extensions',
            name=ext_string,
            invoke_on_load=True,
        )
        return mgr.driver.execute(image_obj)
    except NoMatches:
        pass
