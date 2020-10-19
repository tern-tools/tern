# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Environment prep before analysis and cleanup after
"""

import logging
import os
import shutil

from tern.utils import constants
from tern.utils import general
from tern.utils import rootfs
from tern.utils import cache

# global logger
logger = logging.getLogger(constants.logger_name)


def setup(working_dir=None):
    """Environment setup
    working_dir: a directory path other than the default directory"""
    # create the top directory and cache file
    logger.debug("Setting up...")
    top_dir = general.get_top_dir(working_dir)
    if not os.path.isdir(top_dir):
        os.makedirs(top_dir)
    # set the working directory according to user input
    rootfs.set_working_dir(working_dir)
    # load the cache
    cache.load()


def teardown(keep=False):
    """Tear down the environment setup"""
    logger.debug("Tearing down...")
    # save the cache
    cache.save()
    # clean up the working directory if user has not asked to keep it
    if not keep:
        clean_working_dir()
    else:
        logger.debug(
            "Working directory available at: %s", rootfs.get_working_dir())


def clean_image_tars(image_obj):
    """Given an image object, clean up all the image layer contents"""
    for layer in image_obj.layers:
        fspath = rootfs.get_untar_dir(layer.tar_file)
        if os.path.exists(fspath):
            rootfs.root_command(rootfs.remove, fspath)


def clean_working_dir():
    """Clean up the working directory"""
    path = rootfs.get_working_dir()
    if os.path.exists(path):
        shutil.rmtree(path)
