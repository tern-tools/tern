# -*- coding: utf-8 -*-
#
# Copyright (c) 2021-2022 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Interactions with remote container images using skopeo
"""

import json
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


def pull_image(image_tag_string, no_tls=False):
    """Use skopeo to pull a remote image into the working directory"""
    # Check if skopeo is set up
    check_skopeo_setup()
    # we will assume the docker transport for now
    remote = f'docker://{image_tag_string}'
    if len(image_tag_string.split(':')) > 2:
        remote = image_tag_string
    local = f'dir:{rootfs.get_working_dir()}'
    logger.debug("Attempting to pull image \"%s\"", image_tag_string)
    if no_tls:
        result, error = rootfs.shell_command(
            False, ['skopeo', 'copy', '--src-tls-verify=false', remote, local])
    else:
        result, error = rootfs.shell_command(
            False, ['skopeo', 'copy', remote, local])
    if error:
        logger.error("Error when downloading image: \"%s\"", error)
        return None
    return result


def get_image_digest(image_tag_string):
    """Use skopeo to get the remote image's digest"""
    # check if skopeo is set up
    check_skopeo_setup()
    remote = f'docker://{image_tag_string}'
    logger.debug("Inspecting remote image \"%s\"", image_tag_string)
    result, error = rootfs.shell_command(
        False, ['skopeo', 'inspect', remote])
    if error or not result:
        logger.error("Unable to retrieve image digest")
        return None, None
    result_string = json.loads(result)
    digest_string = result_string.get("Digest")
    if not digest_string:
        logger.error("No image digest available")
        return None, None
    digest_list = digest_string.split(":")
    return digest_list[0], digest_list[1]
