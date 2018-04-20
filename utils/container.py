'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''
import grp
import io
import logging
import os
import pwd
import subprocess
import tarfile
import time


from .constants import container
from .constants import logger_name
from .constants import temp_folder

from .general import pushd

'''
Container operations
'''
# docker commands
check_images = ['docker', 'images']
pull = ['docker', 'pull']
build = ['docker', 'build']
run = ['docker', 'run', '-td']
check_running = ['docker', 'ps', '-a']
copy = ['docker', 'cp']
execute = ['docker', 'exec']
inspect = ['docker', 'inspect']
stop = ['docker', 'stop']
remove = ['docker', 'rm']
delete = ['docker', 'rmi', '-f']
save = ['docker', 'save']

# docker container names
# TODO: randomly generated image and container names
# image = const.image
tag = str(int(time.time()))

# global logger
logger = logging.getLogger(logger_name)


def docker_command(command, *extra):
    '''Invoke docker command. If the command fails nothing is returned
    If it passes then the result is returned'''
    full_cmd = []
    sudo = True
    try:
        members = grp.getgrnam('docker').gr_mem
        if pwd.getpwuid(os.getuid()).pw_name in members:
            sudo = False
    except KeyError:
        pass
    if sudo:
        full_cmd.append('sudo')
    full_cmd.extend(command)
    for arg in extra:
        full_cmd.append(arg)
    # invoke
    logger.debug("Running command: " + ' '.join(full_cmd))
    pipes = subprocess.Popen(full_cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    result, error = pipes.communicate()
    if error:
        raise subprocess.CalledProcessError(1, cmd=full_cmd, output=error)
    else:
        return result


def check_container():
    '''Check if a container exists'''
    is_container = False
    keyvalue = 'name=' + container
    result = docker_command(check_running, '--filter', keyvalue)
    result_lines = result.decode('utf-8').split('\n')
    if len(result_lines) > 2:
        is_container = True
    return is_container


def check_image(image_tag_string):
    '''Check if image exists'''
    is_image = False
    result = docker_command(check_images, image_tag_string)
    result_lines = result.decode('utf-8').split('\n')
    if len(result_lines) > 2:
        is_image = True
    return is_image


def pull_image(image_tag_string):
    '''Try to pull an image from Dockerhub'''
    is_there = False
    try:
        result = docker_command(pull, image_tag_string)
        print(result)
        is_there = True
    except subprocess.CalledProcessError as error:
        print(error.output)
        is_there = False
    return is_there


def build_container(dockerfile, image_tag_string):
    '''Invoke docker command to build a docker image from the dockerfile
    It is assumed that docker is installed and the docker daemon is running'''
    curr_path = os.getcwd()
    path = os.path.dirname(dockerfile)
    if not check_image(image_tag_string):
        with pushd(path):
            try:
                docker_command(build, '-t', image_tag_string, '-f',
                               os.path.basename(dockerfile), '.')
            except subprocess.CalledProcessError as error:
                os.chdir(curr_path)
                raise subprocess.CalledProcessError(
                    error.returncode, cmd=error.cmd,
                    output=error.output.decode('utf-8'))


def start_container(image_tag_string):
    '''Invoke docker command to start a container
    If one already exists then stop it
    Use this only in the beginning of running commands within a container
    Assumptions: Docker is installed and the docker daemon is running
    There is no other running container from the given image'''
    if check_container():
        docker_command(stop, container)
        docker_command(remove, container)
    docker_command(run, '--name', container, image_tag_string)


def remove_container():
    '''Remove a running container'''
    if check_container():
        docker_command(stop, container)
        docker_command(remove, container)


def remove_image(image_tag_string):
    '''Remove an image'''
    if check_image(image_tag_string):
        docker_command(delete, image_tag_string)


def get_image_id(image_tag_string):
    '''Get the image ID by inspecting the image'''
    result = docker_command(inspect, "-f'{{json .Id}}'", image_tag_string)
    return result.split(':').pop()


def extract_image_metadata(image_tag_string):
    '''Run docker save and extract the files in a temporary directory'''
    temp_path = os.path.abspath(temp_folder)
    result = docker_command(save, image_tag_string)
    with tarfile.open(fileobj=io.BytesIO(result)) as tar:
        tar.extractall(temp_path)
    if not os.path.exists(temp_path):
        raise IOError('Unable to untar Docker image')
