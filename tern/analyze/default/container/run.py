# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Run analysis on a container image
"""

import logging

from tern.utils import constants
from tern.utils import rootfs
from tern.report import report
from tern.report import formats
from tern import prep
from tern.load import docker_api
from tern.analyze import common
from tern.analyze.default.container import image as cimage


# global logger
logger = logging.getLogger(constants.logger_name)


def extract_image(args):
    """The image can either be downloaded from a container registry or provided
    as an image tarball. Extract the image into a working directory accordingly
    Return an image name and tag and an image digest if it exists"""
    if args.docker_image:
        # extract the docker image
        image_attrs = docker_api.dump_docker_image(args.docker_image)
        if image_attrs:
            # repo name and digest is preferred, but if that doesn't exist
            # the repo name and tag will do. If neither exist use repo Id.
            if image_attrs['Id']:
                image_string = image_attrs['Id']
            if image_attrs['RepoTags']:
                image_string = image_attrs['RepoTags'][0]
            if image_attrs['RepoDigests']:
                image_string = image_attrs['RepoDigests'][0]
            return image_string
        logger.critical("Cannot extract Docker image")
    if args.raw_image:
        # for now we assume that the raw image tarball is always
        # the product of "docker save", hence it will be in
        # the docker style layout
        if rootfs.extract_tarfile(args.raw_image, rootfs.get_working_dir()):
            return args.raw_image
        logger.critical("Cannot extract raw image")
    return None


def setup(image_obj):
    """Setup the image object and anything else for analysis"""
    # Add a Notice object for each layer
    for layer in image_obj.layers:
        origin_str = 'Layer {}'.format(layer.layer_index)
        layer.origins.add_notice_origin(origin_str)
    # Set up working directories and mount points
    rootfs.set_up()


def teardown(image_obj):
    """Teardown and cleanup after analysis"""
    # Add the image layers to the cache
    common.save_to_cache(image_obj)
    # Clean up working directories and mount points
    rootfs.clean_up()


def execute_image(args):
    """Execution path for container images"""
    logger.debug('Starting analysis...')
    image_string = extract_image(args)
    # If the image has been extracted, load the metadata
    if image_string:
        full_image = cimage.load_full_image(
            image_string, args.load_until_layer)
        # check if the image was loaded successfully
        if full_image.origins.is_empty():
            # Add an image origin here
            full_image.origins.add_notice_origin(
                formats.docker_image.format(imagetag=image_string))
            # Set up for analysis
            setup(full_image)
            # analyze image
            cimage.analyze(full_image, args)
            # report out
            report.report_out(args, full_image)
            # clean up
            teardown(full_image)
        else:
            # we cannot load the full image
            logger.error('Cannot retrieve full image metadata')
        if not args.keep_wd:
            prep.clean_image_tars(full_image)
