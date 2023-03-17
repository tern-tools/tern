# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Analyze the container image in default mode
"""

import docker
import logging
import subprocess  # nosec

from tern.classes.notice import Notice
from tern.classes.docker_image import DockerImage
from tern.classes.oci_image import OCIImage
from tern.utils import constants
from tern.analyze import passthrough
from tern.analyze.default.container import single_layer
from tern.analyze.default.container import multi_layer
from tern.report import formats

# global logger
logger = logging.getLogger(constants.logger_name)


def load_full_image(image_tag_string, image_type='oci', load_until_layer=0):
    """Create image object from image name and tag and return the object.
    * The kind of image object is created based on the image_type.
    image_type = oci OR docker
    * Loads only as many layers as needed.
    * Remove docker-daemon prefix for local images"""
    if image_type == 'oci':
        image = OCIImage(image_tag_string.replace('docker-daemon:', ''))
    elif image_type == 'docker':
        image = DockerImage(image_tag_string.replace('docker-daemon:', ''))
    failure_origin = formats.image_load_failure.format(
        testimage=image.repotag)
    try:
        image.load_image(load_until_layer)
    except (NameError,
            subprocess.CalledProcessError,
            IOError,
            docker.errors.APIError,
            ValueError,
            EOFError) as error:
        logger.warning('Error in loading image: %s', str(error))
        image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error), 'error'))
    return image


def default_analyze(image_obj, options):
    """ Steps to analyze a container image (we assume it is a DockerImage
    object for now)
    1. Analyze the first layer to get a baseline list of packages
    2. Analyze subsequent loaded layers
    3. Return the final image with all metadata filled in
    Options:
        redo: do not use the cache; False by default
        driver: mount using the chosen driver;
                If no driver is provided, we will use the kernel's
                overlayfs driver (only available with Linux mainline
                kernel version 4.0 or later)"""
    # set up empty master list of packages
    master_list = []
    # Analyze the first layer and get prerequisites for the next layer
    prereqs = single_layer.analyze_first_layer(image_obj, master_list, options)
    if options.extend:
        # Run the extension that the user has chosen for the first layer
        passthrough.run_extension_layer(image_obj.layers[0], options.extend,
                                        options.redo)
    # Analyze the remaining layers if there are more
    if prereqs and len(image_obj.layers) > 1:
        multi_layer.analyze_subsequent_layers(
            image_obj, prereqs, master_list, options)
    return image_obj
