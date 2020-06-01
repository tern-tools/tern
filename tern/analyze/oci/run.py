# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Execute a OCI format image
"""

import logging
from tern.report import report
from tern.report import formats
from tern.utils import constants
from tern.analyze.passthrough import run_extension
from tern.analyze.oci.analyze import analyze_oci_image

# global logger
logger = logging.getLogger(constants.logger_name)


def analyze(image_obj, args):
    '''
    Analyze the image object either using the default
    method or the extended method
    '''
    if args.extend:
        run_extension(image_obj, args.extend, args.redo)
    else:
        analyze_oci_image(image_obj, args.redo)


def execute_oci_image(args):
    '''Execution path if given a OCI image'''
    logger.debug('Setting up...')
    image_string = args.image
    image_string = image_string.split("://")[1]
    image_string = image_string.split(":")[0]
    report.setup(image_tag_string=image_string, image_type=args.type)
    # attempt to get built image metadata
    full_image = report.load_oci_image(image_string)
    if full_image.origins.is_empty():
        # image loading was successful
        # Add an image origin here
        full_image.origins.add_notice_origin(
            formats.oci_image.format(imagetag=image_string))
        # analyze image
        analyze(full_image, args)
        # generate report
        report.report_out(args, full_image)
    else:
        # we cannot load the full image
        logger.warning('Cannot retrieve full image metadata')
    if not args.keep_wd:
        report.clean_image_tars(full_image)
    logger.debug('Teardown...')
    report.teardown()
    if not args.keep_wd:
        report.clean_working_dir()
