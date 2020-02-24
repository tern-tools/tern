# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Docker container operations
"""

import docker
import grp
import logging
import os
import pwd
import requests
import sys
import time

from tern.utils.constants import container
from tern.utils.constants import logger_name
from tern.utils.constants import temp_tarfile
from tern.utils import rootfs
from tern.utils import general


# timestamp tag
tag = str(int(time.time()))

# global logger
logger = logging.getLogger(logger_name)

# global docker client
client = None


def check_docker_setup():
    '''Check if the docker daemon is running and if the user has the
    appropriate privileges'''
    global client
    try:
        client = docker.from_env()
        client.ping()
    except requests.exceptions.ConnectionError as e:
        logger.critical('Critical Docker error: %s', str(e))
        if 'FileNotFoundError' in str(e):
            logger.critical('Docker is not installed or the daemon is not '
                            'running.')
        if 'PermissionError' in str(e):
            logger.critical('The user id is not in the docker group.')
        logger.critical('Aborting...')
        sys.exit(1)


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
    logger.debug(
        "Checking if image \"%s\" is available on disk...", image_tag_string)
    try:
        image = client.images.get(image_tag_string)
        logger.debug("Image \"%s\" found", image_tag_string)
        return image
    except docker.errors.ImageNotFound:
        return None


def pull_image(image_tag_string):
    '''Try to pull an image from Dockerhub'''
    logger.debug("Attempting to pull image \"%s\"", image_tag_string)
    try:
        image = client.images.pull(image_tag_string)
        logger.debug("Image \"%s\" downloaded", image_tag_string)
        return image
    except docker.errors.ImageNotFound:
        logger.warning("No such image: \"%s\"", image_tag_string)
        return None


def get_image(image_tag_string):
    '''Try to get an image from Dockerhub.
    image_tag_string: can be in image:tag or image@digest_type:digest format'''
    check_docker_setup()
    image = check_image(image_tag_string)
    if image is None:
        return pull_image(image_tag_string)
    return image


def get_image_digest(docker_image):
    '''Given a docker image object return the digest information of the
    unique image in 'image@sha_type:digest' format.'''
    return docker_image.attrs['RepoDigests'][0]


def build_container(dockerfile, image_tag_string):
    '''Invoke docker command to build a docker image from the dockerfile
    It is assumed that docker is installed and the docker daemon is running'''
    path = os.path.dirname(dockerfile)
    if not check_image(image_tag_string):
        # let docker handle the errors
        client.images.build(path=path, tag=image_tag_string, nocache=True)


def start_container(image_tag_string):
    '''Start the test container in detach state'''
    try:
        client.containers.run(image_tag_string, name=container, detach=True)
    except requests.exceptions.HTTPError:
        # container may already be running
        pass
    try:
        remove_container()
        client.containers.run(image_tag_string, name=container, detach=True)
    except requests.exceptions.HTTPError:
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
    temp_path = rootfs.get_working_dir()
    placeholder = os.path.join(general.get_top_dir(), temp_tarfile)
    try:
        if general.check_tar(image_tag_string) is True:
            # image_tag_string is the path to the tar file for raw images
            rootfs.extract_tarfile(image_tag_string, temp_path)
        else:
            image = client.images.get(image_tag_string)
            result = image.save(chunk_size=2097152, named=True)
            # write all of the tar byte stream into temporary tar file
            with open(placeholder, 'wb') as f:
                for chunk in result:
                    f.write(chunk)
            # extract tarfile into folder
            rootfs.extract_tarfile(placeholder, temp_path)
            # remove temporary tar file
            os.remove(placeholder)
        if not os.listdir(temp_path):
            raise IOError('Unable to untar Docker image')
    except docker.errors.APIError:  # pylint: disable=try-except-raise
        raise
