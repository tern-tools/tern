'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging
import os
import subprocess
import sys

from report import content
from report import errors
from utils import container
from utils import constants
from utils import cache
from utils import rootfs
from classes.docker_image import DockerImage
from classes.image import Image
from classes.image_layer import ImageLayer
from classes.notice import Notice
from classes.package import Package
import common
import docker
from command_lib import command_lib

'''
Create a report
'''

# global logger
logger = logging.getLogger(constants.logger_name)


def write_report(report):
    '''Write the report to a file'''
    with open(constants.report_file, 'w') as f:
        f.write(report)


def setup(dockerfile=None):
    '''Any initial setup'''
    # load the cache
    cache.load()
    # load dockerfile if present
    if dockerfile:
        docker.load_docker_commands(dockerfile)
    # create temporary working directory
    if not os.path.exists(constants.temp_folder):
        os.mkdir(constants.temp_folder)
    # set up folders for rootfs operations
    rootfs.set_up()


def teardown():
    '''Clean up everything'''
    # save the cache
    cache.save()
    # remove folders for rootfs operations
    rootfs.clean_up()


def load_base_image():
    '''Create base image from dockerfile instructions and return the image'''
    base_image, dockerfile_lines = docker.get_dockerfile_base()
    # try to get image metadata
    if not container.check_image(base_image.repotag):
        container.pull_image(base_image.repotag)
    try:
        base_image.load_image()
    except NameError as error:
        logger.warning('Error in loading base image: ' + str(error))
        base_image.origins.add_notice_to_origins(
            dockerfile_lines, Notice(str(error), 'error'))
    except subprocess.CalledProcessError as error:
        logger.warning(
            'Error in loading base image: ' + str(error.output, 'utf-8'))
        base_image.origins.add_notice_to_origins(
            dockerfile_lines, Notice(str(error.output, 'utf-8'), 'error'))
    except IOError as error:
        logger.warning('Error in loading base image: ' + str(error))
        base_image.origins.add_notice_to_origin(
            dockerfile_lines, Notice(str(error), 'error'))
    return base_image


def load_full_image():
    '''Create image object from test image and return the object'''
    test_image = DockerImage(docker.get_dockerfile_image_tag())
    try:
        test_image.load_image()
    except NameError as error:
        test_image.origins.add_notice_to_origins(
            test_image.repotag, Notice(str(error), 'error'))
    except subprocess.CalledProcessError as error:
        test_image.origins.add_notice_to_origins(
            test_image.repotag, Notice(str(error.output, 'utf-8'), 'error'))
    except IOError as error:
        test_image.origins.add_notice_to_origins(
            test_image.repotag, Notice(str(error), 'error'))
    return test_image


def analyze_docker_image(image_obj):
    '''Given a DockerImage object, for each layer, retrieve the packages, first
    looking up in cache and if not there then looking up in the command
    library. For looking up in command library first mount the filesystem
    and then look up the command library for commands to run in chroot'''
    shell = ''
    # set the layer that is mounted. In the beginning this is 0
    mounted = 0
    # find the shell by mounting the base layer
    target = rootfs.mount_base_layer(image_obj.layers[0].tar_file)
    binary = common.get_base_bin(image_obj.layers[0])
    # find the shell to invoke commands in
    shell, _ = command_lib.get_image_shell(
        command_lib.get_base_listing(binary))
    if not shell:
        shell = constants.shell
    # only extract packages if there is a known binary and the layer is not
    # cached
    if binary and not common.load_from_cache(image_obj.layers[0]):
        # get the packages of the first layer
        rootfs.prep_rootfs(target)
        common.add_base_packages(image_obj.layers[0], binary)
        # unmount proc, sys and dev
        rootfs.undo_mount()
    else:
        logger.warning(errors.unrecognized_base.format(
            image_name=image_obj.name, image_tag=image_obj.tag))
    # get packages for subsequent layers
    curr_layer = 1
    while curr_layer < len(image_obj.layers):
        if not common.load_from_cache(image_obj.layers[curr_layer]):
            # mount from the layer after the mounted layer till the current
            # layer
            for index in range(mounted + 1, curr_layer + 1):
                target = rootfs.mount_diff_layer(
                    image_obj.layers[index].tar_file)
            mounted = curr_layer
            # mount dev, sys and proc after mounting diff layers
            rootfs.prep_rootfs(target)
            docker.add_packages_from_history(
                image_obj.layers[curr_layer], shell)
            rootfs.undo_mount()
        curr_layer = curr_layer + 1
    # undo all the mounts
    rootfs.unmount_rootfs(mounted + 1)
    common.save_to_cache(image_obj)


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
    for inst in docker.docker_commands:
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
    logger.debug('Writing report...')
    report = ''
    if args.summary:
        for image in images:
            report = report + content.print_summary_report(image)
    else:
        for image in images:
            report = report + content.print_full_report(image)
    write_report(report)


def execute_dockerfile(args):
    '''Execution path if given a dockerfile'''
    logger.debug('Setting up...')
    try:
        container.docker_command(['docker', 'ps'])
    except subprocess.CalledProcessError as error:
        logger.error('Docker daemon is not running: {0}'.format(
            error.output.decode('utf-8')))
        sys.exit()
    setup(args.dockerfile)
    # attempt to build the image
    logger.debug('Building Docker image...')
    # placeholder to check if we can analyze the full image
    completed = True
    build, msg = docker.is_build()
    if build:
        # attempt to get built image metadata
        full_image = load_full_image()
        if full_image.origins.is_empty():
            # image loading was successful
            # analyze image
            analyze_docker_image(full_image)
        else:
            # we cannot load the full image
            logger.warning('Cannot retrieve full image metadata')
            completed = False
        # clean up image
        container.remove_image(full_image.repotag)
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
            # analyze image
            analyze_docker_image(base_image)
        else:
            # we cannot load the base image
            logger.warning('Cannot retrieve base image metadata')
        # run through commands in the Dockerfile
        logger.debug('Parsing Dockerfile to generate report...')
        stub_image = get_dockerfile_packages()
        # clean up image
        container.remove_image(base_image.repotag)
    # generate report based on what images were created
    if completed:
        generate_report(args, full_image)
    else:
        generate_report(args, base_image, stub_image)
    logger.debug('Cleaning up...')
    teardown()
