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
import json
from dateutil import parser
from datetime import datetime
from tern.utils.constants import container
from tern.utils.constants import logger_name
from tern.utils.constants import temp_tarfile
from tern.utils import rootfs
from tern.utils import general
from tern.utils.constants import docker_endpoint, temp_folder


# timestamp tag
tag = str(int(time.time()))

# global logger
logger = logging.getLogger(logger_name)

# global docker client
client = None
auth_token = None


def check_docker_setup():
    '''Check if the docker daemon is running and if the user has the
    appropriate privileges'''
    global client
    try:
        client = docker.from_env(timeout=120)
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
        logger.debug("Downloading Image \"%s\"", image_tag_string)
        image = save_image(image_tag_string)
        logger.debug("Image saved \"%s\"", image_tag_string)
        logger.debug("Image \"%s\" downloaded", image_tag_string)
        return image
    except Exception as ex:
        logger.warning(ex)
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
    path = os.path.dirname(os.path.abspath(dockerfile))
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
    except docker.errors.APIError as e:
        raise docker.errors.APIError(e)


def close_client():
    '''End docker interactions by closing the client. This is meant to be
    used after analysis is done'''
    try:
        client.close()
    except (AttributeError, requests.exceptions.ConnectionError):
        # it should either already be closed, no socker is in use,
        # or docker is not setup -- either way, the socket is closed
        pass


def save_image(image_tag_string):
    '''Download and save a docker image with given name and tag '''
    rootfs.create_working_dir()
    temp_path = os.path.join(rootfs.mount_dir, temp_folder)
    image_name, image_tag = image_tag_string.split(":")
    manifest = pull_image_manifest(image_name, image_tag)
    manifest_path = os.path.join(temp_path, "manifest.json")
    # saving image manifest
    json.dump(manifest, open(manifest_path, "w"))

    digest = manifest.get("config").get("digest")
    config = pull_image_config(image_name, image_tag, digest)
    config_name = digest.split(":")[1]
    config_path = os.path.join(temp_path, config_name)
    # saving image config
    json.dump(config, open(config_path, "w"))

    # saving image layers
    layers = manifest.get("layers")
    for layer, content in pull_image_layers(image_name, image_tag, layers):
        layer_path = os.path.join(temp_path, layer)
        with open(layer_path, "wb") as layer_content:
            layer_content.write(content)

    return temp_path


def generate_manifest_url(image_name, image_tag):
    '''
    Generate a docker image manifest url end point with
    given image name and tag
    '''
    url = "{0}/{1}/manifests/{2}"
    return url.format(docker_endpoint, image_name, image_tag)


def generage_image_blobs_url(image_name, digest):
    '''
    Generate a docker image blobs url end point with
    given image name and tag
    '''
    url = "{0}/{1}/blobs/{2}"
    return url.format(docker_endpoint, image_name, digest)


def is_token_expired():
    '''method to validtae if Docker HTTP Rest API auth token is expired'''
    global auth_token
    token_expires_in = int(auth_token.get("expires_in"))
    token_issued_at = auth_token.get("issued_at")
    start = datetime.timestamp(parser.isoparse(token_issued_at))
    end = datetime.timestamp(datetime.now())

    if end - start > token_expires_in:
        return True

    return False


def generate_auth_token(image_name, image_tag):
    '''
    method to generate Docker HTTP Rest API auth token
    for given image_name and image_tag
    '''
    global auth_token
    url = generate_manifest_url(image_name, image_tag)
    response = requests.get(url)
    authentication = response.headers.get("Www-Authenticate").split(",")
    auth_url, params = None, dict()
    for line in authentication:
        if "Bearer realm" in line:
            auth_url = json.loads(line.split("=")[1])
        if "service" in line:
            params["service"] = json.loads(line.split("=")[1])
        if "scope" in line:
            params["scope"] = json.loads(line.split("=")[1])
    response = requests.get(auth_url, params=params)
    if response.status_code != 200:
        raise Exception(response.text)

    auth_token = response.json()


def pull_image_manifest(image_name, image_tag):
    '''download and return the image manifest'''
    global auth_token
    url = generate_manifest_url(image_name, image_tag)
    generate_auth_token(image_name, image_tag)
    token_value = auth_token.get("token")
    headers = dict()
    headers['Authorization'] = 'Bearer {0}'.format(token_value)
    headers['Accept'] = 'application/vnd.docker.distribution.manifest.v2+json'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.text)

    return response.json()


def pull_image_layers(image_name, image_tag, layers):
    '''Given manifest data, saves the image layers inside mount dir'''
    global auth_token
    headers = dict()
    headers['Accept'] = 'application/vnd.docker.image.rootfs.diff.tar.gzip'
    for layer in layers:
        digest = layer.get("digest")
        url = generage_image_blobs_url(image_name, digest)
        # to generate token if it is expired while downloading a layer
        if is_token_expired():
            generate_auth_token(image_name, image_tag)
        token_value = auth_token.get("token")
        headers['Authorization'] = 'Bearer {0}'.format(token_value)
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(response.text)
        layer_name = digest.split(":")[1]
        yield layer_name, response.text.encode()


def pull_image_config(image_name, image_tag, digest):
    '''Given manifest data, return the image config digest'''
    global auth_token
    url = generage_image_blobs_url(image_name, digest)
    if is_token_expired():
        generate_auth_token(image_name, image_tag)
    token_value = auth_token.get("token")
    headers = dict()
    headers['Authorization'] = 'Bearer {0}'.format(token_value)
    headers['Accept'] = 'application/vnd.docker.container.image.v1+json'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(response.text)

    return response.json()
