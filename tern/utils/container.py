# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Docker container operations
"""

import docker
import grp
import logging
import os
import pwd
import tarfile
import time
from requests.exceptions import HTTPError


from tern.utils.constants import container
from tern.utils.constants import logger_name
from tern.utils.constants import temp_folder
from tern.utils.constants import temp_tarfile


# timestamp tag
tag = str(int(time.time()))

# global logger
logger = logging.getLogger(logger_name)

# global docker client
client = None
try:
    client = docker.from_env()
except IOError:
    logger.critical("Docker daemon not running")
    raise Exception("Critical Error using Docker API. See logs for details")
except OSError:  # pylint: disable=duplicate-except
    logger.critical("User has no access to docker unix socket")
    raise Exception("Critical Error using Docker API. See logs for details")


def is_sudo():
    '''Check if the user uses sudo for docker commands'''
    sudo = True
    try:
        members = grp.getgrnam('docker').gr_mem
        if pwd.getpwuid(os.getuid()).pw_name in members:
            sudo = False
    except KeyError:
        pass
    return sudo


def check_container():
    '''Check is the test container is running'''
    try:
        client.containers.get(container)
        return True
    except docker.errors.NotFound:
        return False


def check_image(image_tag_string):
    '''Check if image exists'''
    logger.debug("Checking if image \"%s\" is available on disk...",
        image_tag_string)
    try:
        client.images.get(image_tag_string)
        logger.debug("Image \"%s\" found", image_tag_string)
        return True
    except docker.errors.ImageNotFound:
        return False


def pull_image(image_tag_string):
    '''Try to pull an image from Dockerhub'''
    logger.debug("Attempting to pull image \"%s\"", image_tag_string)
    try:
        client.images.pull(image_tag_string)
        logger.debug("Image \"%s\" downloaded", image_tag_string)
        return True
    except docker.errors.ImageNotFound:
        logger.warning("No such image: \"%s\"", image_tag_string)
        return False


def build_container(dockerfile, image_tag_string):
    '''Invoke docker command to build a docker image from the dockerfile
    It is assumed that docker is installed and the docker daemon is running'''
    path = os.path.dirname(dockerfile)
    if not check_image(image_tag_string):
        try:
            client.images.build(path=path, tag=image_tag_string, nocache=True)
        except (TypeError, docker.errors.APIError, docker.errors.BuildError):  # pylint: disable=try-except-raise
            raise


def start_container(image_tag_string):
    '''Start the test container in detach state'''
    try:
        client.containers.run(image_tag_string, name=container, detach=True)
    except HTTPError:
        # container may already be running
        pass
    try:
        remove_container()
        client.containers.run(image_tag_string, name=container, detach=True)
    except HTTPError:
        # not sure what the error is now
        raise Exception("Cannot remove running container")


def remove_container():
    '''Remove the running test container'''
    active_c = client.containers.get(container)
    active_c.stop()
    active_c.remove()


def remove_image(image_tag_string):
    '''Remove an image'''
    if check_image(image_tag_string):
        client.images.remove(image_tag_string)


def get_image_id(image_tag_string):
    '''Get the image ID by inspecting image and tag'''
    try:
        image = client.images.get(image_tag_string)
        return image.id.split(':').pop()
    except docker.errors.ImageNotFound:
        return ''


def extract_image_metadata(image_tag_string):
    '''Run docker save and extract the files in a temporary directory'''
    temp_path = os.path.abspath(temp_folder)
    try:
        image = client.images.get(image_tag_string)
        result = image.save(chunk_size=2097152, named=True)
        # write all of the tar byte stream into temporary tar file
        with open(temp_tarfile, 'wb') as f:
            for chunk in result:
                f.write(chunk)
        # extract tarfile into folder
        with tarfile.open(temp_tarfile) as tar:
            tar.extractall(temp_path)
        # remove temporary tar file
        os.remove(temp_tarfile)
        if not os.path.exists(temp_path):
            raise IOError('Unable to untar Docker image')
    except docker.errors.APIError:  # pylint: disable=try-except-raise
        raise
