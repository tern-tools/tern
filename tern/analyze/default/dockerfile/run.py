# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Run analysis on a Dockerfile
"""

import docker
import logging
import os
import subprocess  # nosec

from tern.utils import constants
from tern.utils import rootfs
from tern.classes.notice import Notice
from tern.classes.image_layer import ImageLayer
from tern.classes.image import Image
from tern.classes.package import Package
from tern.load import docker_api
from tern import prep
from tern.analyze import common
from tern.analyze.default import filter as fltr
from tern.analyze.default.dockerfile import parse
from tern.analyze.default.dockerfile import lock
from tern.analyze.default.container import run as crun
from tern.analyze.default.container import image as cimage
from tern.report import report
from tern.report import formats


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
    for cmd in lock.docker_commands:
        if cmd['instruction'] == 'RUN':
            layer_count = layer_count + 1
            layer = ImageLayer(layer_count)
            install_commands, msg = fltr.filter_install_commands(cmd['value'])
            if msg:
                layer.origins.add_notice_to_origins(
                    cmd['value'], Notice(msg, 'info'))
            pkg_names = []
            for command in install_commands:
                pkg_names.append(fltr.get_installed_package_names(command))
            for pkg_name in pkg_names:
                pkg = Package(pkg_name)
                # shell parser does not parse version pins yet
                # when that is enabled, Notices for no versions need to be
                # added here
                layer.add_package(pkg)
    return stub_image


def analyze_full_image(full_image, redo, driver, extension):
    """If we are able to load a full image after a build, we can run an
    analysis on it"""
    # set up for analysis
    crun.setup(full_image)
    # analyze image
    cimage.analyze(full_image, redo, driver, extension)
    # clean up after analysis
    rootfs.clean_up()
    # we should now be able to set imported layers
    lock.set_imported_layers(full_image)
    # save to the cache
    common.save_to_cache(full_image)
    return [full_image]


def load_base_image():
    '''Create base image from dockerfile instructions and return the image'''
    base_image, dockerfile_lines = lock.get_dockerfile_base()
    # try to get image metadata
    if docker_api.dump_docker_image(base_image.repotag):
        # now see if we can load the image
        try:
            base_image.load_image()
        except (NameError,
                subprocess.CalledProcessError,
                IOError,
                docker.errors.APIError,
                ValueError,
                EOFError) as error:
            logger.warning('Error in loading base image: %s', str(error))
            base_image.origins.add_notice_to_origins(
                dockerfile_lines, Notice(str(error), 'error'))
        return base_image
    return None


def analyze_base_image(base_image, redo, driver, extension):
    """If we are unable to load the full image, we will try to analyze
    the base image and try to extrapolate"""
    # set up for analysis
    crun.setup(base_image)
    # analyze image
    cimage.analyze(base_image, redo, driver, extension)
    # clean up
    rootfs.clean_up()
    # save the base image to cache
    common.save_to_cache(base_image)
    # let's try to figure out what packages were going to be installed in
    # the dockerfile anyway
    stub_image = get_dockerfile_packages()
    return [base_image, stub_image]


def full_image_analysis(dfile, redo, driver, keep, extension):
    """This subroutine is executed when a Dockerfile is successfully built"""
    image_list = []
    # attempt to load the built image metadata
    full_image = cimage.load_full_image(dfile)
    if full_image.origins.is_empty():
        # Add an image origin here
        full_image.origins.add_notice_origin(
            formats.dockerfile_image.format(dockerfile=dfile))
        image_list = analyze_full_image(full_image, redo, driver, extension)
    else:
        # we cannot analyze the full image, but maybe we can
        # analyze the base image
        logger.error('Cannot retrieve full image metadata')
    # cleanup for full images
    if not keep:
        prep.clean_image_tars(full_image)
    return image_list


def base_and_run_analysis(dfile, redo, driver, keep, extension):
    """This subroutine is executed when a Dockerfile fails build. It returns
    a base image and any RUN commands in the Dockerfile."""
    image_list = []
    # Try to analyze the base image
    logger.debug('Analyzing base image...')
    # this will pull, dump and load the base image
    base_image = load_base_image()
    if base_image:
        if base_image.origins.is_empty():
            # add a notice stating failure to build image
            base_image.origins.add_notice_to_origins(dfile, Notice(
                formats.image_build_failure, 'warning'))
            image_list = analyze_base_image(
                base_image, redo, driver, extension)
        else:
            # we cannot load the base image
            logger.warning('Cannot retrieve base image metadata')
        # cleanup for base images
        if not keep:
            prep.clean_image_tars(base_image)
    else:
        logger.error('Cannot analyze base image')
    return image_list


def analyze_single_dockerfile(dockerfile, redo, driver, keep_wd, extend):
    """Run image analysis for a single Dockerfile. Return a list of images.
    Inputs are:
        dockerfile: the Dockerfile file
        redo: True if analysis needs to be redone
        driver: The filesystem driver used
        keep_wd: True if the working directory must not be cleaned up
        extend: the extension used for analysis"""
    # attempt to build the image
    logger.debug('Building Docker image with Dockerfile: %s', dockerfile)
    image_info = docker_api.build_and_dump(dockerfile)
    image_list = []
    if image_info:
        logger.debug('Docker image successfully built. Analyzing...')
        # analyze the full image
        image_list = full_image_analysis(
            dockerfile, redo, driver, keep_wd, extend)
    else:
        # cannot build the image
        logger.warning('Cannot build image')
        # analyze the base image and any RUN lines in the Dockerfile
        image_list = base_and_run_analysis(
            dockerfile, redo, driver, keep_wd, extend)
    return image_list


def execute_dockerfile(args, locking=False):
    """Execution path for Dockerfiles"""
    dfile = ''
    if locking:
        dfile = args.lock
    else:
        dfile = args.dockerfile
    image_list = []
    logger.debug("Parsing Dockerfile...")
    dfobj = parse.get_dockerfile_obj(dfile)
    # expand potential ARG values so base image tag is correct
    parse.expand_arg(dfobj)
    parse.expand_vars(dfobj)
    # Store dockerfile path and commands so we can access it during execution
    lock.load_docker_commands(dfobj)
    if dfobj.is_multistage:
        image_list = analyze_multistage_dockerfile(
            dfobj, args.redo, args.driver, args.keep_wd, args.extend)
    else:
        image_list = analyze_single_dockerfile(
            dfile, args.redo, args.driver, args.keep_wd, args.extend)
    # generate report based on what images were created
    if image_list:
        if not locking:
            report.report_out(args, *image_list)
        else:
            logger.debug('Generating locked Dockerfile...')
            # we can only lock one image for now
            locked_dfobj = lock.lock_dockerfile(dfobj, image_list[0])
            output = lock.create_locked_dockerfile(locked_dfobj)
            lock.write_locked_dockerfile(output, args.output_file)


def write_dockerfile_stages(dfobj):
    """Given a Dockerfile object, create Dockerfiles for each of the
    stages for analysis. Return a list of Dockerfiles"""
    stages = parse.get_dockerfile_stages(dfobj)
    dockerfiles = []
    filepath, filename = os.path.split(dfobj.filepath)
    for stage in stages:
        stagefile = os.path.join(
            filepath, '{}_{}'.format(filename, stages.index(stage) + 1))
        with open(stagefile, 'w') as f:
            f.write(stage)
        dockerfiles.append(stagefile)
    return dockerfiles


def clean_dockerfile_stages(dockerfiles):
    """Remove all the intermediate dockerfiles"""
    for dockerfile in dockerfiles:
        os.remove(dockerfile)


def analyze_multistage_dockerfile(dfobj, redo, driver, keep_wd, extend):
    """Split the multistage dockerfile, and then analyze on each stage.
    Inputs:
        dfobj: the Dockerfile object
        redo: True when we want to redo the analysis
        driver: the filesystem driver to use
        keep_wd: keep working directory
        extend: the extension to use for analysis"""
    # split the multistage dockerfile into single stages for analysis
    dockerfiles = write_dockerfile_stages(dfobj)
    image_list = []
    for dfile in dockerfiles:
        imlist = analyze_single_dockerfile(
            dfile, redo, driver, keep_wd, extend)
        image_list.extend(imlist)
    clean_dockerfile_stages(dockerfiles)
    # finally build the existing Dockerfile
    finallist = analyze_single_dockerfile(
        dfobj.filepath, redo, driver, keep_wd, extend)
    image_list.extend(finallist)
    return image_list
