# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Analyze a Docker container image
"""

import logging
import sys

from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs
from tern.classes.notice import Notice
from tern.analyze import common
import tern.analyze.docker.helpers as dhelper
from tern.command_lib import command_lib
from tern.analyze.docker import dockerfile as d_file


# global logger
logger = logging.getLogger(constants.logger_name)


def analyze_docker_image(image_obj, redo=False, dfile_lock=False, dfobj=None,
                         driver=None):
    '''Given a DockerImage object, for each layer, retrieve the packages, first
    looking up in cache and if not there then looking up in the command
    library. For looking up in command library first mount the filesystem
    and then look up the command library for commands to run in chroot.
    If there's a dockerfile object available, extract any package
    information from the layers.'''

    # set up empty master list of packages
    master_list = []
    prepare_for_analysis(image_obj, dfobj)
    # Analyze the first layer and get the shell
    shell = analyze_first_layer(image_obj, master_list, redo)
    # Analyze the remaining layers
    analyze_subsequent_layers(image_obj, shell, master_list, redo, dfobj,
                              dfile_lock, driver)
    common.save_to_cache(image_obj)


def prepare_for_analysis(image_obj, dfobj):
    # find the layers that are imported
    if dfobj:
        dhelper.set_imported_layers(image_obj)
    # add notices for each layer if it is imported
    image_setup(image_obj)
    # set up the mount points
    rootfs.set_up()


def abort_analysis():
    '''Abort due to some external event'''
    rootfs.recover()
    sys.exit(1)


def image_setup(image_obj):
    '''Add notices for each layer'''
    for layer in image_obj.layers:
        origin_str = 'Layer {}'.format(layer.layer_index)
        layer.origins.add_notice_origin(origin_str)
        if layer.import_str:
            layer.origins.add_notice_to_origins(origin_str, Notice(
                'Imported in Dockerfile using: ' + layer.import_str, 'info'))
