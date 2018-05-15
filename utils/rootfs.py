'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''
import logging
import os
import subprocess
import tarfile

from . import constants
'''
Operations to mount container filesystems and run commands against them
'''

# remove root filesystems
remove = ['rm', '-rf']

# mount commands
mount = ['mount', '-o', 'bind']
mount_proc = ['mount', '-t', 'proc', '/proc']
mount_sys = ['mount', '-o', 'bind', '/sys']
mount_dev = ['mount', '-o', 'bind', '/dev']
unmount = ['umount']

# enable host DNS settings
host_dns = ['cp', constants.resolv_path]

# unshare PID within rootfs
unshare_pid = ['unshare', '-pf']

# union mount
union_mount = ['mount', '-t', 'overlay', 'overlay', '-o']

# global logger
logger = logging.getLogger(constants.logger_name)


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


def get_untar_dir(layer_tarfile):
    '''get the directory to untar the layer tar file'''
    return os.path.join(constants.temp_folder, os.path.dirname(
        layer_tarfile), constants.untar_dir)


def set_up():
    '''Create required directories'''
    workdir_path = os.path.join(constants.temp_folder, constants.workdir)
    mergedir_path = os.path.join(constants.temp_folder, constants.mergedir)
    if not os.path.isdir(workdir_path):
        os.mkdir(workdir_path)
    if not os.path.isdir(mergedir_path):
        os.mkdir(mergedir_path)


def extract_layer_tar(layer_tar_path, directory_path):
    '''Assuming all the metadata for an image has been extracted into the
    temp folder, extract the tarfile into the required directory'''
    with tarfile.open(layer_tar_path) as tar:
        tar.extractall(directory_path)


def prep_rootfs(rootfs_dir):
    '''Mount required filesystems in the rootfs directory'''
    rootfs_path = os.path.abspath(rootfs_dir)
    try:
        root_command(mount_proc, os.path.join(rootfs_path, 'proc'))
        root_command(mount_sys, os.path.join(rootfs_path, 'sys'))
        root_command(mount_dev, os.path.join(rootfs_path, 'dev'))
        root_command(host_dns, os.path.join(
            rootfs_path, constants.resolv_path[1:]))
    except subprocess.CalledProcessError as error:
        logger.error(error.output)
        raise


def mount_base_layer(base_layer_tar):
    '''To mount to base layer:
        1. Untar the base layer tar file
        2. Mount into mergedir
        3. Prepare all the mounts'''
    base_rootfs_path = get_untar_dir(base_layer_tar)
    source_dir_path = os.path.join(constants.temp_folder, base_layer_tar)
    target_dir_path = os.path.join(constants.temp_folder, constants.mergedir)
    if os.path.isdir(base_rootfs_path):
        root_command(remove, base_rootfs_path)
    extract_layer_tar(source_dir_path, base_rootfs_path)
    root_command(mount, base_rootfs_path, target_dir_path)
    prep_rootfs(target_dir_path)


def mount_diff_layer(diff_layer_tar):
    '''To mount the diff layer:
        1. Untar the diff rootfs
        2. Union mount this directory on the mergedir
        3. Prepare all the mounts'''
    upper_dir_path = get_untar_dir(diff_layer_tar)
    source_dir_path = os.path.join(constants.temp_folder, diff_layer_tar)
    merge_dir_path = os.path.join(constants.temp_folder, constants.mergedir)
    workdir_path = os.path.join(constants.temp_folder, constants.workdir)
    if os.path.isdir(upper_dir_path):
        root_command(remove, upper_dir_path)
    extract_layer_tar(source_dir_path, upper_dir_path)
    args = 'lowerdir=' + merge_dir_path + ',upperdir=' + upper_dir_path + \
        ',workdir=' + workdir_path
    root_command(union_mount, args, merge_dir_path)
    prep_rootfs(merge_dir_path)


def run_chroot_command(command_string, shell):
    '''Run the command string in a chroot jail within the rootfs namespace'''
    target_dir = os.path.join(constants.temp_folder, constants.mergedir)
    mount_proc = '--mount-proc=' + os.path.join(
        os.path.abspath(target_dir), 'proc')
    result = root_command(unshare_pid, mount_proc, 'chroot', target_dir,
                          shell, '-c', command_string)
    return result


def undo_mount():
    '''Unmount proc, sys, and dev directories'''
    rootfs_path = os.path.join(constants.temp_folder, constants.mergedir)
    root_command(unmount, os.path.join(rootfs_path, 'proc'))
    root_command(unmount, os.path.join(rootfs_path, 'sys'))
    root_command(unmount, os.path.join(rootfs_path, 'dev'))


def unmount_rootfs():
    '''Unmount the overlay filesystem'''
    rootfs_path = os.path.join(constants.temp_folder, constants.mergedir)
    root_command(unmount, '-rl', rootfs_path)


def clean_up():
    '''Remove all the setup directories'''
    mergedir_path = os.path.join(constants.temp_folder, constants.mergedir)
    workdir_path = os.path.join(constants.temp_folder, constants.workdir)
    root_command(remove, mergedir_path)
    root_command(remove, workdir_path)
