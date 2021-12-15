# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Interactions with remote container images using skopeo
"""

import logging
import sys
import shutil

from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def check_skopeo_setup():
    """Check if the skopeo tool is installed"""
    if not shutil.which('skopeo'):
        logger.critical('Skopeo is not installed')
        logger.critical('Exiting...')
        sys.exit(1)


def pull_image(image_tag_string):
    """Use skopeo to pull a remote image into the working directory"""
    # Check if skopeo is set up
    check_skopeo_setup()
    # we will assume the docker transport for now
    remote = f'docker://{image_tag_string}'
    local = f'dir:{rootfs.get_working_dir()}'
    logger.debug("Attempting to pull image \"%s\"", image_tag_string)
    result, error = rootfs.shell_command(
        False, ['skopeo', 'copy', remote, local])
    if error:
        logger.error("Error when downloading image: \"%s\"", error)
        return None
    return result
