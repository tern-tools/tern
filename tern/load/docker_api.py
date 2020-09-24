# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Interactions with the Docker daemon
"""

import docker
import logging
import os
import requests
import sys
import time

from tern.utils import constants
from tern.utils import rootfs
from tern.utils import general

# global logger
logger = logging.getLogger(constants.logger_name)


def check_docker_setup():
    """Check if the docker daemon is up and running. This should return a
    docker client if everything is running fine. Else it should exit
    gracefully. The intent is that this function is run before any docker
    operations are invoked"""
    try:
        client = docker.from_env(timeout=120)
        client.ping()
        return client
    except requests.exceptions.ConnectionError as e:
        logger.critical('Critical Docker error: %s', str(e))
        if 'FileNotFoundError' in str(e):
            logger.critical('Docker is not installed or the daemon is not '
                            'running.')
        if 'PermissionError' in str(e):
            logger.critical('The user id is not in the docker group.')
        logger.critical('Aborting...')
        sys.exit(1)


def build_image(dockerfile, client):
    """Invoke docker build with the given dockerfile. It is assumed that
    docker is installed and the docker daemon is running"""
    df_path = os.path.abspath(dockerfile)
    image_tag = '{name}:{tag}'.format(name=constants.image,
                                      tag=str(int(time.time())))
    # try to build the image
    try:
        with open(df_path, 'rb') as f:
            image_obj, _ = client.images.build(fileobj=f,
                                               tag=image_tag,
                                               nocache=True,
                                               forcerm=True)
            return image_obj
    except FileNotFoundError as e:
        logger.critical('Dockerfile not found: %s', e)
        return None
    except (docker.errors.BuildError, docker.errors.APIError) as e:
        logger.warning('Build failed: %s', e)
        return None


def extract_image(image_obj):
    """Run docker save and extract the resulting tarball into the working
    directory."""
    temp_path = rootfs.get_working_dir()
    placeholder = os.path.join(general.get_top_dir(), constants.temp_tarfile)
    # try to save the image
    try:
        result = image_obj.save(chunk_size=2097152, named=True)
        # write all of the tar byte stream into temporary tar file
        with open(placeholder, 'wb') as f:
            for chunk in result:
                f.write(chunk)
        # extract temporary tar file into the working directory
        rootfs.extract_tarfile(placeholder, temp_path)
        # remove the tar file
        os.remove(placeholder)
        # If these operations didn't work, return False
        if not os.listdir(temp_path):
            logger.critical('Unable to extract Docker image')
            return False
        return True
    except docker.errors.APIError as e:
        logger.critical(
            'Something happened with the Docker client: %s', e)
        return False


def remove_image(image_obj, client):
    """Remove the Docker container image"""
    try:
        for tag in image_obj.tags:
            client.images.remove(tag)
        return True
    except docker.errors.APIError as e:
        logger.warning(
            'Unable to remove the image: %s', e)
        return False


def close_client(client):
    """End docker interactions by closing the client. This is meant to be
    used after loading of the image is done"""
    try:
        client.close()
    except (AttributeError, requests.exceptions.ConnectionError):
        # it should either already be closed, no socket is in use,
        # or docker is not setup -- either way, the socket is closed
        pass
