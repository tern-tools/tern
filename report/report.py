'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging
import subprocess

from report import content
from utils import container
from utils import constants
from utils import cache
from classes.docker_image import DockerImage
from classes.image import Image
from classes.image_layer import ImageLayer
from classes.notice import Notice
from classes.package import Package
from command_lib import command_lib as cmdlib
import common
import docker

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


def load_base_image():
    '''Create base image from dockerfile instructions and return the image'''
    base_image, dockerfile_lines = docker.get_dockerfile_base()
    # try to get image metadata
    if container.check_image(base_image.repotag):
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


def execute_dockerfile(args):
    '''Execution path if given a dockerfile'''
    logger.debug('Setting up...')
    setup(args.dockerfile)
    dockerfile_parse = False
    # try to get Docker base image metadata
    logger.debug('Loading base image...')
    base_image = load_base_image()
    logger.debug('Base image loaded...')
    # check if the base image added any notices
    if base_image.origins.is_empty():
        # load any packages from cache
        logger.debug('Looking up cache for base image layers...')
        if not common.load_from_cache(base_image):
            # load any packages using the command library
            logger.debug('Retrieving metadata using scripts from base.yml')
            container.start_container(base_image.repotag)
            common.add_base_packages(base_image)
            container.remove_container()
            logger.debug('Saving base image layers...')
            common.save_to_cache(base_image)
            cache.save()
        # attempt to get the packages for the rest of the image
        # since we only have a dockerfile, we will attempt to build the
        # image first
        # This step actually needs to go to the beginning but since
        # there is no way of tracking imported images from within
        # the docker image history, we build after importing the base image
        shell, msg = cmdlib.get_image_shell(
            cmdlib.get_base_listing(base_image.name, base_image.tag))
        if not shell:
            shell = constants.shell
        logger.debug('Building image...')
        build, msg = docker.is_build()
        if build:
            # attempt to get built image metadata
            full_image = load_full_image()
            if full_image.origins.is_empty():
                # link layer to imported base image
                full_image.set_image_import(base_image)
                if not common.load_from_cache(full_image):
                    # find packages per layer
                    container.start_container(full_image.repotag)
                    logger.debug('Retrieving metadata using scripts from '
                                 'snippets.yml')
                    docker.add_packages_from_history(full_image, shell)
                    container.remove_container()
                    # record missing layers in the cache
                    common.save_to_cache(full_image)
                    cache.save()
            else:
                # we cannot extract the built image's metadata
                dockerfile_parse = True
            report = content.print_full_report(full_image)
            logger.debug('Cleaning up...')
            container.remove_image(full_image.repotag)
            logger.debug('Writing report...')
            write_report(report)
        else:
            # we cannot build the image
            common.record_image_layers(base_image)
            dockerfile_parse = True
    else:
        # something went wrong in getting the base image
        dockerfile_parse = True
    # check if the dockerfile needs to be parsed
    if dockerfile_parse:
        logger.debug('Parsing Dockerfile to generate report...')
        stub_image = get_dockerfile_packages()
        report = content.print_full_report(base_image)
        report = report + content.print_full_report(stub_image)
        write_report(report)
    logger.debug('Cleaning up...')
    container.remove_image(full_image.repotag)
    cache.save()
