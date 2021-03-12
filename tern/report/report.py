# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Create a report
"""

import logging
import os
import shutil
from stevedore import driver
from stevedore.exception import NoMatches

from tern.utils import constants
from tern.utils import rootfs

# global logger
logger = logging.getLogger(constants.logger_name)


def write_report(report, args):
    '''Write the report to a file'''
    if args.output_file:
        file_name = args.output_file
    with open(file_name, 'w') as f:
        f.write(report)


def clean_image_tars(image_obj):
    '''Clean up untar directories'''
    for layer in image_obj.layers:
        fspath = rootfs.get_untar_dir(layer.tar_file)
        if os.path.exists(fspath):
            rootfs.root_command(rootfs.remove, fspath)


def clean_working_dir():
    '''Clean up the working directory
    If bind_mount is true then leave the upper level directory'''
    path = rootfs.get_working_dir()
    if os.path.exists(path):
        shutil.rmtree(path)


def generate_report(args, *images):
    '''Generate a report based on the command line options'''
    if args.report_format:
        return generate_format(
            images, args.report_format, args.print_inclusive)
    return generate_format(images, 'default', args.print_inclusive)


def generate_format(images, format_string, print_inclusive):
    '''Generate a report in the format of format_string given one or more
    image objects. Here we will load the required module and run the generate
    function to get back a report'''
    try:
        mgr = driver.DriverManager(
            namespace='tern.formats',
            name=format_string,
            invoke_on_load=True,
        )
        return mgr.driver.generate(images, print_inclusive)
    except NoMatches:
        pass


def generate_format_layer(layer, format_string):
    """Generate a report in the format of format_string given one layer
    object. This is similar to the generate_format function"""
    try:
        mgr = driver.DriverManager(
            namespace='tern.formats',
            name=format_string,
            invoke_on_load=True,
        )
        return mgr.driver.generate_layer(layer)
    except NoMatches:
        pass


def report_out(args, *images):
    for img in images:
        if (args.load_until_layer > img.total_layers and
                args.load_until_layer != 0):
            # The actual ignoring is done in docker_image.py
            # Warning is given here for visibility to user
            logger.warning(f'Given layer {args.load_until_layer} exceeds total'
                           + f' number of layers in image ({img.total_layers})'
                           + '. Ignoring --layer option and generating report '
                           + 'for'
                           + f' {img.total_layers} total layers')
    report = generate_report(args, *images)
    if not report:
        logger.error("%s not a recognized plugin.", args.report_format)
    elif args.output_file:
        write_report(report, args)
    else:
        print(report)


def report_layer(layer, args):
    """Generate a report for one layer object"""
    layer_report = ""
    if args.report_format:
        layer_report = generate_format_layer(layer, args.report_format)
    else:
        layer_report = generate_format_layer(layer, 'default')
    if not layer_report:
        logger.error(
            "Unable to generate %s report type for layer", args.report_format)
    else:
        if args.output_file:
            write_report(layer_report, args)
        else:
            print(layer_report)
