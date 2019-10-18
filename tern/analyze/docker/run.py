# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Execute a Docker container image
"""

import logging

from tern.report import formats
from tern.report import report
from tern.utils import constants
from tern.analyze.docker import container
from tern.classes.notice import Notice
from tern.analyze import common
import tern.analyze.docker.helpers as dhelper
from tern.classes.image_layer import ImageLayer
from tern.classes.image import Image
from tern.classes.package import Package
from tern.analyze.docker.analyze import analyze_docker_image
from tern.analyze.passthrough import run_extension


# global logger
logger = logging.getLogger(constants.logger_name)


def get_dockerfile_packages():
    '''Given a Dockerfile return an approximate image object. This is mosty
    guess work and shouldn't be relied on for accurate information. Add
    Notice messages indicating as such:
        1. Create an image with a placeholder repotag
        2. For each RUN command, create a package list
        3. Create layer objects with incremental integers and add the package
        list to that layer with a Notice about parsing
        4. Return stub image'''
    stub_image = Image('easteregg:cookie')
    layer_count = 0
    for inst in dhelper.docker_commands:
        if inst[0] == 'RUN':
            layer_count = layer_count + 1
            layer = ImageLayer(layer_count)
            install_commands, msg = common.filter_install_commands(inst[1])
            if msg:
                layer.origins.add_notice_to_origins(
                    inst[1], Notice(msg, 'info'))
            pkg_names = []
            for command in install_commands:
                pkg_names.append(common.get_installed_package_names(command))
            for pkg_name in pkg_names:
                pkg = Package(pkg_name)
                # shell parser does not parse version pins yet
                # when that is enabled, Notices for no versions need to be
                # added here
                layer.add_package(pkg)
    return stub_image


def analyze(image_obj, args, is_dockerfile=False):
    '''Analyze the image object either using the default method or the extended
    method'''
    if args.extend:
        run_extension(image_obj, args.extend)
    else:
        analyze_docker_image(image_obj, args.redo, is_dockerfile)


def execute_docker_image(args):
    '''Execution path if given a Docker image'''
    logger.debug('Setting up...')
    image_string = args.docker_image
    if not args.raw_image:
        # don't check docker daemon for raw images
        container.check_docker_setup()
    else:
        image_string = args.raw_image
    report.setup(image_tag_string=image_string)
    # attempt to get built image metadata
    full_image = report.load_full_image(image_string)
    if full_image.origins.is_empty():
        # image loading was successful
        # Add an image origin here
        full_image.origins.add_notice_origin(
            formats.docker_image.format(imagetag=image_string))
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
        report.clean_working_dir(args.bind_mount)


def execute_dockerfile(args):
    '''Execution path if given a dockerfile'''
    container.check_docker_setup()
    logger.debug('Setting up...')
    report.setup(dockerfile=args.dockerfile)
    # attempt to build the image
    logger.debug('Building Docker image...')
    # placeholder to check if we can analyze the full image
    completed = True
    build, _ = dhelper.is_build()
    if build:
        # attempt to get built image metadata
        image_tag_string = dhelper.get_dockerfile_image_tag()
        full_image = report.load_full_image(image_tag_string)
        if full_image.origins.is_empty():
            # image loading was successful
            # Add an image origin here
            full_image.origins.add_notice_origin(
                formats.dockerfile_image.format(dockerfile=args.dockerfile))
            # analyze image
            analyze(full_image, args, True)
        else:
            # we cannot load the full image
            logger.warning('Cannot retrieve full image metadata')
            completed = False
        # clean up image
        container.remove_image(full_image.repotag)
        if not args.keep_wd:
            report.clean_image_tars(full_image)
    else:
        # cannot build the image
        logger.warning('Cannot build image')
        completed = False
    # check if we have analyzed the full image or not
    if not completed:
        # get the base image
        logger.debug('Loading base image...')
        base_image = report.load_base_image()
        if base_image.origins.is_empty():
            # image loading was successful
            # add a notice stating failure to build image
            base_image.origins.add_notice_to_origins(
                args.dockerfile, Notice(
                    formats.image_build_failure, 'warning'))
            # analyze image
            analyze(base_image, args)
        else:
            # we cannot load the base image
            logger.warning('Cannot retrieve base image metadata')
        # run through commands in the Dockerfile
        logger.debug('Parsing Dockerfile to generate report...')
        stub_image = get_dockerfile_packages()
        if not args.keep_wd:
            report.clean_image_tars(base_image)
    # generate report based on what images were created
    if completed:
        report.report_out(args, full_image)
    else:
        report.report_out(args, base_image, stub_image)
    logger.debug('Teardown...')
    report.teardown()
    if not args.keep_wd:
        report.clean_working_dir(args.bind_mount)
