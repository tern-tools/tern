# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Create a report
"""

import logging
import os
import shutil
import subprocess  # nosec
import sys

from stevedore import driver
from stevedore.exception import NoMatches

from tern.report import errors
from tern.report import formats
from tern.analyze.docker import container
from tern.analyze import common
from tern.utils import constants
from tern.utils import cache
from tern.utils import general
from tern.utils import rootfs
from tern.classes.docker_image import DockerImage
from tern.classes.notice import Notice
import tern.analyze.docker.helpers as dhelper

# global logger
logger = logging.getLogger(constants.logger_name)


def write_report(report, args):
    '''Write the report to a file'''
    if args.output_file:
        file_name = args.output_file
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
    if image_tag_string and common.check_tar(image_tag_string) is False:
        if not container.check_image(image_tag_string):
            # if no docker image is present, try to pull it
            if not container.pull_image(image_tag_string):
                logger.fatal("%s", errors.cannot_find_image.format(
                    imagetag=image_tag_string))
                sys.exit()


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
    path = rootfs.get_working_dir()
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
    except (NameError,
            subprocess.CalledProcessError,
            IOError,
            ValueError,
            EOFError) as error:
        logger.warning('Error in loading base image: %s', str(error))
        base_image.origins.add_notice_to_origins(
            dockerfile_lines, Notice(str(error), 'error'))
    return base_image


def load_full_image(image_tag_string):
    '''Create image object from image name and tag and return the object'''
    test_image = DockerImage(image_tag_string)
    failure_origin = formats.image_load_failure.format(
        testimage=test_image.repotag)
    try:
        test_image.load_image()
    except (NameError,
            subprocess.CalledProcessError,
            IOError,
            ValueError,
            EOFError) as error:
        logger.warning('Error in loading image: %s', str(error))
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error), 'error'))
    return test_image


def generate_report(args, *images):
    '''Generate a report based on the command line options'''
    if args.report_format:
        return generate_format(images, args.report_format)
    return generate_format(images, 'default')


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
    elif args.output_file:
        write_report(report, args)
    else:
        print(report)
