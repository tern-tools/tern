'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging

from utils import container
from utils import constants
from utils import cache
from classes.docker_image import DockerImage
import common
import docker

'''
Create a report
'''

def write_report(report):
    '''Write the report to a file'''
    with open(const.report_file, 'w') as f:
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
    base_image = docker.get_dockerfile_base()
    base_instructions_str = docker.print_dockerfile_base()
    # try to get image metadata
    if check_image(base_image.repotag):
        try:
            base_image.load_image()
        except NameError as error:
            name_error_notice = Notice(
                base_instructions_str, str(error), 'error')
            base_image.add_notice(name_error_notice)
        except subprocess.CalledProcessError as error:
            docker_exec_notice = Notice(
                base_instructions_str, str(error.output, 'utf-8'), 'error')
            base_image.add_notice(docker_exec_notice)
        except IOError as error:
            extract_error_notice = Notice(
                base_instructions_str, str(error), 'error')
            base_image.add_notice(extract_error_notice)
    return base_image


def load_full_image():
    '''Create image object from test image and return the object'''
    test_image = DockerImage(docker.get_dockerfile_image_tag())
    try:
        test_image.load_image()
    except NameError as error:
        name_error_notice = Notice(test_image.repotag, str(error), 'error')
        test_image.add_notice(name_error_notice)
    except subprocess.CalledProcessError as error:
        docker_exec_notice = Notice(
            test_image.repotag, str(error.output, 'utf-8'), 'error')
        test_image.add_notice(docker_exec_notice)
    except IOError as error:
        extract_error_notice = Notice(test_image.repotag, str(error), 'error')
        base_image.add_notice(extract_error_notice)
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


def execute_dockerfile(args):
    '''Execution path if given a dockerfile'''
    # logging
    logger = logging.getLogger(constants.logger_name)
    setup(args.dockerfile)
    dockerfile_parse = False
    # try to get Docker base image metadata
    base_image = load_base_image()
    if len(base_image.notices) == 0:
        # load any packages from cache
        if not common.load_from_cache(base_image):
            # load any packages using the command library
            container.start_container(base_image.repotag)
            common.add_base_packages(base_image)
            container.remove_container()
        # attempt to get the packages for the rest of the image
        # since we only have a dockerfile, we will attempt to build the
        # image first
        # This step actually needs to go to the beginning but since
        # there is no way of tracking imported images from within
        # the docker image history, we build after importing the base image
        build, msg = docker.is_build()
        if build:
            # attempt to get built image metadata
            full_image = load_full_image()
            if len(full_image.notices) == 0:
                # load from Docker history
            else:
                # we cannot extract the built image's metadata
                dockerfile_parse = True
        else:
            # we cannot build the image
            dockerfile_parse = True
    else:
        # something went wrong in getting the base image
        dockerfile_parse = True
