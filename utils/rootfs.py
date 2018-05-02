'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''
import logging
import os
import subprocess
import shutil
import tarfile

from .constants import resolv_path
from .constants import logger_name
from .constants import temp_folder
from .constants import workdir
from .constants import upperdir

'''
Operations to mount container filesystems and run commands against them
'''

# mount commands
mount_proc = ['mount', '-t', 'proc', '/proc']
mount_sys = ['mount', '-o', 'bind', '/sys']
mount_dev = ['mount', '-o', 'bind', '/dev']
mount_run = ['mount', '-o', 'bind', '/run']
unmount = ['umount']

# enable host DNS settings
host_dns = ['cp', resolv_path]

# unshare PID within rootfs
unshare_pid = ['unshare', '-pf']

# union mount
union_mount = ['mount', '-t', 'overlay', 'overlay', '-o']

# global logger
logger = logging.getLogger(logger_name)


def root_command(command, *extra):
    '''Invoke a shell command as root or using sudo. The command is a
    list of shell command words'''
    full_cmd = []
    sudo = True
    if os.getuid() == 0:
        sudo = False
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


def extract_layer_tar(layer_tar, directory):
    '''Assuming all the metadata for an image has been extracted into the
    temp folder, extract the tarfile into the required directory'''
    tarfile_path = os.path.abspath(
        os.path.join(temp_folder, layer_tar))
    with tarfile.open(tarfile_path) as tar:
        tar.extractall(directory)


def prep_rootfs(rootfs_dir):
    '''Mount required filesystems in the rootfs directory'''
    rootfs_path = os.path.abspath(rootfs_dir)
    try:
        root_command(mount_proc, os.path.join(rootfs_path, 'proc'))
        root_command(mount_sys, os.path.join(rootfs_path, 'sys'))
        root_command(mount_dev, os.path.join(rootfs_path, 'dev'))
        root_command(mount_run, os.path.join(rootfs_path, 'run'))
        root_command(host_dns, os.path.join(
            rootfs_path, resolv_path[1:]))
    except subprocess.CalledProcessError as error:
        logger.error(error.output)


def mount_base_layer(base_rootfs):
    '''To mount to base layer:
        1. Untar the base rootfs into the working directory
        2. Prepare all the mounts'''
    extract_layer_tar(base_rootfs, workdir)
    prep_rootfs(workdir)


def mount_diff_layer(diff_rootfs):
    '''To mount the diff layer:
        1. Untar the diff rootfs into the upper directory
        2. Union mount this directory on the working directory
        3. Prepare all the mounts'''
    extract_layer_tar(diff_rootfs, upperdir)
    args = 'lowerdir=' + workdir + ',upperdir=' + upperdir + ',workdir=' + \
        workdir
    root_command(union_mount, args, workdir)
    prep_rootfs(workdir)


def run_chroot_command(command_string, shell):
    '''Run the command string in a chroot jail within the rootfs namespace'''
    mount_proc = '--mount-proc=' + os.path.join(
        os.path.abspath(workdir), 'proc')
    result = root_command(
        unshare_pid, mount_proc, 'chroot', workdir, shell, '-c', command_string)
    return result


def clean_up():
    '''Clean up all the directories'''
    workdir_path = os.path.abspath(workdir)
    upperdir_path = os.path.abspath(upperdir)
    root_command(unmount, '-r', workdir_path)
    root_command(unmount, os.path.join(workdir_path, 'proc'))
    root_command(unmount, os.path.join(workdir_path, 'sys'))
    root_command(unmount, os.path.join(workdir_path, 'dev'))
    root_command(unmount, os.path.join(workdir_path, 'run'))
    shutil.rmtree(workdir_path)
    shutil.rmtree(upperdir_path)
