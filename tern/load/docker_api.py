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


def build_image(dfile, client):
    """Invoke docker build with the given dockerfile. It is assumed that
    docker is installed and the docker daemon is running"""
    df_path = os.path.abspath(dfile)
    image_tag = '{name}:{tag}'.format(name=constants.image,
                                      tag=str(int(time.time())))
    # try to build the image
    # TODO: docker's upstream API does not support build
    # contexts yet. You are expected to provide that as
    # a tarball as of the 4.3.1 release
    # This is a hack to get around that
    # source:
    # https://github.com/docker/docker-py/issues/2105#issuecomment-613685891
    dfcontents = ''
    dfcontext = os.path.dirname(df_path)
    try:
        with open(df_path) as f:
            dfcontents = f.read()
        # terrible bypass of the API
        docker.api.build.process_dockerfile = lambda dockerfile, path: (
            df_path, dockerfile)
        image_obj, _ = client.images.build(
            tag=image_tag, path=dfcontext, dockerfile=dfcontents, nocache=True,
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


def build_and_dump(dockerfile):
    """Given a path to the dockerfile, use the Docker API to build the
    container image and extract the image into a working directory. Return
    true if this succeeded and false if it didn't"""
    image_metadata = None
    # open up a client first
    # if this fails we cannot proceed further so we will exit
    client = check_docker_setup()
    image = build_image(dockerfile, client)
    if image:
        # the build succeeded, so we should be able to extract it
        if extract_image(image):
            image_metadata = image.attrs
            remove_image(image, client)
    else:
        # we didn't succeed building the image
        logger.warning("Could not build Docker image")
    close_client(client)
    return image_metadata


# These functions should be deprecated
def check_image(image_tag_string, client):
    """Check if the image and tag exist on disk"""
    logger.debug(
        "Checking if image \"%s\" is available on disk...", image_tag_string)
    try:
        image_obj = client.images.get(image_tag_string)
        logger.debug("Image \"%s\" found", image_tag_string)
        return image_obj
    except docker.errors.ImageNotFound:
        return None


def pull_image(image_tag_string, client):
    """Pull an image from a container registry using Docker
    Note: this function uses the Docker API to pull from a container
    registry and is not responsible for configuring what registry to use"""
    logger.debug("Attempting to pull image \"%s\"", image_tag_string)
    try:
        image = client.images.pull(image_tag_string)
        logger.debug("Image \"%s\" downloaded", image_tag_string)
        return image
    except (docker.errors.ImageNotFound, docker.errors.NotFound):
        logger.error("No such image: \"%s\"", image_tag_string)
        return None


def get_docker_image(image_tag_string, client):
    """Try to retrieve a docker image using the docker API.
    image_tag_string: can be in image:tag or image@digest_type:digest format"""
    image = check_image(image_tag_string, client)
    if image is None:
        image = pull_image(image_tag_string, client)
    return image


def get_docker_image_digest(image_tag):
    """Given an image and tag, get the image's digest in
    'image@sha_type:digest' format"""
    digest = ""
    # open up a client first
    # if this fails we cannot proceed further so we will exit
    client = check_docker_setup()
    # get the image
    image = get_docker_image(image_tag, client)
    if image:
        digest = image.attrs['RepoDigests'][0]
    # cleanup
    remove_image(image, client)
    close_client(client)
    return digest


def dump_docker_image(image_tag):
    """Given an image and tag or image and digest, use the Docker API to get
    a container image representation into the working directory"""
    image_metadata = None
    # open up a client first
    # if this fails we cannot proceed further so we will exit
    client = check_docker_setup()
    image = get_docker_image(image_tag, client)
    if image:
        if extract_image(image):
            image_metadata = image.attrs
    # now the client can be closed
    close_client(client)
    return image_metadata
