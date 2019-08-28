# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Create a report
"""

import docker
import logging
import os
import shutil
import subprocess  # nosec
import sys

from stevedore import driver
from stevedore.exception import NoMatches

from tern.report import content
from tern.report import errors
from tern.report import formats
from tern.report.analyze import analyze_docker_image
from tern.utils import container
from tern.utils import constants
from tern.utils import cache
from tern.utils import general
from tern.utils import rootfs
from tern.classes.docker_image import DockerImage
from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.classes.notice import Notice
from tern.classes.package import Package
from tern.helpers import common
import tern.helpers.docker as dhelper

# global logger
logger = logging.getLogger(constants.logger_name)


def write_report(report, args):
    '''Write the report to a file'''
    if args.file:
        file_name = args.file
    else:
        file_name = constants.report_file
    with open(file_name, 'w') as f:
        f.write(report)


def setup(dockerfile=None, image_tag_string=None):
    '''Any initial setup'''
    # generate random names for image, container, and tag
    general.initialize_names()
    # load the cache
    cache.load()
    # load dockerfile if present
    if dockerfile:
        dhelper.load_docker_commands(dockerfile)
    # check if the docker image is present
    if image_tag_string:
        if not container.check_image(image_tag_string):
            # if no docker image is present, try to pull it
            if not container.pull_image(image_tag_string):
                logger.fatal("%s", errors.cannot_find_image.format(
                    imagetag=image_tag_string))
                sys.exit()
    # create temporary working directory
    if not os.path.exists(constants.temp_folder):
        os.mkdir(constants.temp_folder)
    # set up folders for rootfs operations
    rootfs.set_up()


def teardown():
    '''Tear down tern setup'''
    # save the cache
    cache.save()
    # remove folders for rootfs operations
    rootfs.clean_up()


def clean_image_tars(image_obj):
    '''Clean up untar directories'''
    for layer in image_obj.layers:
        fspath = rootfs.get_untar_dir(layer.tar_file)
        if os.path.exists(fspath):
            rootfs.root_command(rootfs.remove, fspath)


def clean_working_dir(bind_mount):
    '''Clean up the working directory
    If bind_mount is true then leave the upper level directory'''
    path = os.path.abspath(constants.temp_folder)
    if os.path.exists(path):
        if bind_mount:
            # clean whatever is in temp_folder without removing the folder
            inodes = os.listdir(path)
            for inode in inodes:
                dir_path = os.path.join(path, inode)
                if os.path.isdir(dir_path):
                    shutil.rmtree(dir_path)
                else:
                    os.remove(dir_path)
        else:
            shutil.rmtree(path)


def load_base_image():
    '''Create base image from dockerfile instructions and return the image'''
    base_image, dockerfile_lines = dhelper.get_dockerfile_base()
    # try to get image metadata
    if not container.check_image(base_image.repotag):
        # if no base image is found, give a warning and continue
        if not container.pull_image(base_image.repotag):
            logger.warning("%s", errors.cannot_find_image.format(
                imagetag=base_image.repotag))
    try:
        base_image.load_image()
    except NameError as error:
        logger.warning('Error in loading base image: %s', str(error))
        base_image.origins.add_notice_to_origins(
            dockerfile_lines, Notice(str(error), 'error'))
    except subprocess.CalledProcessError as error:
        logger.warning(
            'Error in loading base image: %s', str(error.output, 'utf-8'))
        base_image.origins.add_notice_to_origins(
            dockerfile_lines, Notice(str(error.output, 'utf-8'), 'error'))
    except IOError as error:
        logger.warning('Error in loading base image: %s', str(error))
        base_image.origins.add_notice_to_origin(
            dockerfile_lines, Notice(str(error), 'error'))
    return base_image


def load_full_image(image_tag_string):
    '''Create image object from image name and tag and return the object'''
    test_image = DockerImage(image_tag_string)
    failure_origin = formats.image_load_failure.format(
        testimage=test_image.repotag)
    try:
        test_image.load_image()
    except NameError as error:
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error), 'error'))
    except subprocess.CalledProcessError as error:
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error.output, 'utf-8'), 'error'))
    except IOError as error:
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error), 'error'))
    return test_image


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


def generate_report(args, *images):
    '''Generate a report based on the command line options'''
    if args.report_format:
        return generate_format(images, args.report_format)
    if args.summary:
        return generate_verbose(True, images)
    return generate_verbose(False, images)


def generate_verbose(is_summary, images):
    '''Generate a verbose report'''
    report = formats.disclaimer.format(
        version_info=content.get_tool_version())
    if is_summary:
        logger.debug('Creating a summary of components in image...')
        for image in images:
            report = report + content.print_summary_report(image)
    else:
        logger.debug('Creating a detailed report of components in image...')
        for image in images:
            report = report + content.print_full_report(image)
    return report


def generate_format(images, format_string):
    '''Generate a report in the format of format_string given one or more
    image objects. Here we will load the required module and run the generate
    function to get back a report'''
    try:
        mgr = driver.DriverManager(
            namespace='tern.formats',
            name=format_string,
            invoke_on_load=True,
        )
        return mgr.driver.generate(images)
    except NoMatches:
        pass

def report_out(args, *images):
    report = generate_report(args, *images)
    if not report:
        logger.error("%s not a recognized plugin.", args.report_format)
    elif args.file:
        write_report(report, args)
    else:
        print(report)


def check_docker_daemon():
    '''Check if the Docker daemon is running. If not, exit gracefully'''
    try:
        docker.from_env()
    except IOError as error:
        logger.error('Docker daemon is not running: %s',
                     error.output.decode('utf-8'))
        sys.exit()


def execute_dockerfile(args):
    '''Execution path if given a dockerfile'''
    check_docker_daemon()
    logger.debug('Setting up...')
    setup(dockerfile=args.dockerfile)
    # attempt to build the image
    logger.debug('Building Docker image...')
    # placeholder to check if we can analyze the full image
    completed = True
    build, _ = dhelper.is_build()
    if build:
        # attempt to get built image metadata
        image_tag_string = dhelper.get_dockerfile_image_tag()
        full_image = load_full_image(image_tag_string)
        if full_image.origins.is_empty():
            # image loading was successful
            # Add an image origin here
            full_image.origins.add_notice_origin(
                formats.dockerfile_image.format(dockerfile=args.dockerfile))
            # analyze image
            analyze_docker_image(full_image, args.redo, True)
        else:
            # we cannot load the full image
            logger.warning('Cannot retrieve full image metadata')
            completed = False
        # clean up image
        container.remove_image(full_image.repotag)
        if not args.keep_working_dir:
            clean_image_tars(full_image)
    else:
        # cannot build the image
        logger.warning('Cannot build image')
        completed = False
    # check if we have analyzed the full image or not
    if not completed:
        # get the base image
        logger.debug('Loading base image...')
        base_image = load_base_image()
        if base_image.origins.is_empty():
            # image loading was successful
            # add a notice stating failure to build image
            base_image.origins.add_notice_to_origins(
                args.dockerfile, Notice(
                    formats.image_build_failure, 'warning'))
            # analyze image
            analyze_docker_image(base_image, args.redo)
        else:
            # we cannot load the base image
            logger.warning('Cannot retrieve base image metadata')
        # run through commands in the Dockerfile
        logger.debug('Parsing Dockerfile to generate report...')
        stub_image = get_dockerfile_packages()
        # clean up image
        container.remove_image(base_image.repotag)
        if not args.keep_working_dir:
            clean_image_tars(base_image)
    # generate report based on what images were created
    if completed:
        report_out(args, full_image)
    else:
        report_out(args, base_image, stub_image)
    logger.debug('Teardown...')
    teardown()
    if not args.keep_working_dir:
        clean_working_dir(args.bind_mount)


def execute_docker_image(args):
    '''Execution path if given a Docker image'''
    check_docker_daemon()
    logger.debug('Setting up...')
    setup(image_tag_string=args.docker_image)
    # attempt to get built image metadata
    full_image = load_full_image(args.docker_image)
    if full_image.origins.is_empty():
        # image loading was successful
        # Add an image origin here
        full_image.origins.add_notice_origin(
            formats.docker_image.format(imagetag=args.docker_image))
        # analyze image
        analyze_docker_image(full_image, args.redo)
        # generate report
        report_out(args, full_image)
    else:
        # we cannot load the full image
        logger.warning('Cannot retrieve full image metadata')
    if not args.keep_working_dir:
        clean_image_tars(full_image)
    logger.debug('Teardown...')
    teardown()
    if not args.keep_working_dir:
        clean_working_dir(args.bind_mount)
