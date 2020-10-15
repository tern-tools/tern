# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Run analysis on a container image or Dockerfile
"""

import logging

from tern.report import formats
from tern.utils import constants
from tern.utils import rootfs
from tern import prep
from tern.load import docker_api
from tern.analyze.default.analyze_image import analyze
from tern.classes.notice import Notice
from tern.analyze import common
import tern.analyze.docker.helpers as dhelper
from tern.classes.image_layer import ImageLayer
from tern.classes.image import Image
from tern.classes.package import Package
from tern.analyze.passthrough import run_extension
from tern.analyze.docker import dockerfile


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
    for cmd in dhelper.docker_commands:
        if cmd['instruction'] == 'RUN':
            layer_count = layer_count + 1
            layer = ImageLayer(layer_count)
            install_commands, msg = \
                common.filter_install_commands(cmd['value'])
            if msg:
                layer.origins.add_notice_to_origins(
                    cmd['value'], Notice(msg, 'info'))
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


def extract_image(args):
    """The image can either be downloaded from a container registry or provided
    as an image tarball. Extract the image into a working directory accordingly
    Return an image name and tag and an image digest if it exists"""
    if args.docker_image:
        # extract the docker image
        image_attrs = docker_api.dump_docker_image(args.docker_image)
        if image_attrs:
            if image_attrs['RepoTags']:
                image_string = image_attrs['RepoTags'][0]
            if image_attrs['RepoDigests']:
                image_digest = image_attrs['RepoDigests'][0]
            return image_string, image_digest
        else:
            logger.critical("Cannot extract Docker image")
            return None, None
    if args.raw_image:
        # for now we assume that the raw image tarball is always
        # the product of "docker save", hence it will be in
        # the docker style layout
        if rootfs.extract_tarfile(args.raw_image, rootfs.get_working_dir()):
            return args.raw_image, None
        else:
            logger.critical("Cannot extract raw image")
            return None, None


def execute_image(args):
    """Execution path for container images"""
    logger.debug('Starting analysis...')
    image_string, image_digest = extract_image(args)
    # If the image has been extracted, load the metadata
    if image_string:
        full_image = image.load_full_image(image_string, image_digest)
        # check if the image was loaded successfully
        if full_image.origins.is_empty():
            # Add an image origin here
            full_image.origins.add_notice_origin(
                formats.docker_image.format(imagetag=image_string))
            # analyze image
            image.analyze(full_image, args)
            # report out
            report.report_out(args, full_image)
        else:
            # we cannot load the full image
            logger.error('Cannot retrieve full image metadata')
    # cleanup
    if not args.keep_wd:
        prep.clean_image_tars(full_image)


def execute_dockerfile(args):  # noqa C901,R0912
    '''Execution path if given a dockerfile'''
    dfile = ''
    dfile_lock = False
    if args.name == 'report':
        dfile = args.dockerfile
    else:
        dfile = args.lock
        dfile_lock = True
    logger.debug("Parsing Dockerfile...")
    dfobj = dockerfile.get_dockerfile_obj(dfile)
    # expand potential ARG values so base image tag is correct
    dockerfile.expand_arg(dfobj)
    dockerfile.expand_vars(dfobj)
    # Store dockerfile path and commands so we can access it during execution
    dhelper.load_docker_commands(dfobj)
    # attempt to build the image
    logger.debug('Building Docker image...')
    image_info = docker_api.build_and_dump(dfile)
    if image_info:
        # attempt to load the built image metadata
        full_image = report.load_full_image(dfile, '')
        if full_image.origins.is_empty():
            # image loading was successful
            # Add an image origin here
            full_image.origins.add_notice_origin(
                formats.dockerfile_image.format(dockerfile=dfile))
            # analyze image
            analyze(full_image, args, dfile_lock, dfobj)
            completed = True
        else:
            # we cannot analyze the full image, but maybe we can
            # analyze the base image
            logger.warning('Cannot retrieve full image metadata')
        # clean up image tarballs
        if not args.keep_wd:
            prep.clean_image_tars(full_image)
    else:
        # cannot build the image
        logger.warning('Cannot build image')
    # check if we have analyzed the full image or not
    if not completed:
        # Try to analyze the base image
        logger.debug('Analyzing base image...')
        base_image = report.load_base_image()
        if base_image.origins.is_empty():
            # image loading was successful
            # add a notice stating failure to build image
            base_image.origins.add_notice_to_origins(
                dfile, Notice(
                    formats.image_build_failure, 'warning'))
            # analyze image
            analyze(base_image, args, dfile_lock, dfobj)
        else:
            # we cannot load the base image
            logger.warning('Cannot retrieve base image metadata')
        stub_image = get_dockerfile_packages()
        if args.name == 'report':
            if not args.keep_wd:
                report.clean_image_tars(base_image)
    # generate report based on what images were created
    if not dfile_lock:
        if completed:
            report.report_out(args, full_image)
        else:
            report.report_out(args, base_image, stub_image)
    else:
        logger.debug('Parsing Dockerfile to generate report...')
        output = dockerfile.create_locked_dockerfile(dfobj)
        dockerfile.write_locked_dockerfile(output, args.output_file)
    # cleanup
    if not args.keep_wd:
        prep.clean_image_tars(full_image)
