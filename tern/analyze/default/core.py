# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Core execution - this is the special sauce of the default operation
"""


import logging
import sys

from tern.report import errors
from tern.utils import constants
from tern.utils import rootfs
from tern.analyze.default.container import image

# global logger
logger = logging.getLogger(constants.logger_name)


def abort_analysis():
    """Abort due to some external event"""
    rootfs.recover()
    sys.exit(1)


def execute_base(layer_obj, shell, binary):
    """Given an ImageLayer object, shell to use and binary, find packages
    installed in the layer using the default method:
        1. Use command_lib's base to look up the binary to see if there
           is a method to retrieve the metadata
        2. If there is, invoke the scripts in a chroot environment and
           process the results
        3. Add the results to the ImageLayer object"""
    try:
        target = rootfs.mount_base_layer(base_layer.tar_file)
        rootfs.prep_rootfs(target)
    except KeyboardInterrupt:
        logger.critical(errors.keyboard_interrupt)
        image.abort_analysis()
    finally:
        # unmount proc, sys and dev
        rootfs.undo_mount()
        rootfs.unmount_rootfs()
