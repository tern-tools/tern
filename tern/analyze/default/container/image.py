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
from tern.utils import rootfs
from tern.utils import general
from tern.classes.notice import Notice
from tern.classes.oci_image import OCIImage
from tern.utils import constants
from tern.analyze import passthrough
from tern.analyze.default.container import single_layer
from tern.analyze.default.container import multi_layer
from tern.report import formats

# global logger
logger = logging.getLogger(constants.logger_name)


def download_container_image(image_tag_string):
    '''Download the docker image and convert it into oci format'''
    try:
        # extract the docker image
        docker_image = image_tag_string
        if 'docker://' in image_tag_string:
            docker_image = image_tag_string.split('docker://')[1]
        image_attr = general.parse_image_string(docker_image)
        oci_image = 'oci://{0}/{1}'.format(
            rootfs.working_dir, image_attr.get('name'))
        docker_image = 'docker://{0}'.format(docker_image)
        # cmd = 'skopeo copy {0} {1}'.format(docker_image, oci_image)
        rootfs.shell_command(False, ['skopeo', 'copy'], docker_image, oci_image)
        # subprocess.check_output(cmd, shell=False)
        return oci_image
    except Exception:
        logger.critical("Cannot extract Docker image")
        raise


def load_full_image(image_tag_string, load_until_layer=0):
    '''Create image object from image name and tag and return the object.
    Loads only as many layers as needed.'''
    test_image = OCIImage(image_tag_string)
    failure_origin = formats.image_load_failure.format(
        testimage=test_image.repotag)
    try:
        test_image.load_image(load_until_layer)
    except (NameError,
            subprocess.CalledProcessError,
            IOError,
            docker.errors.APIError,
            ValueError,
            EOFError) as error:
        logger.warning('Error in loading image: %s', str(error))
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error), 'error'))
    return test_image


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
    # Analyze the remaining layers if there are more
    if prereqs and len(image_obj.layers) > 1:
        multi_layer.analyze_subsequent_layers(
            image_obj, prereqs, master_list, options)
    return image_obj


def analyze(image_obj, options):
    """Either analyze a container image using the default method or pass
    analysis to an external tool"""
    if options.extend:
        passthrough.run_extension(image_obj, options.extend, options.redo)
    else:
        default_analyze(image_obj, options)
