# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Operations to mount container filesystems and run commands against them
"""
import hashlib
import logging
import os
import shutil
import subprocess  # nosec
import pkg_resources

from tern.utils import constants
from tern.utils import general

# remove root filesystems
remove = ['rm', '-rf']

# tar commands
check_tar = ['tar', '-tf']
extract_tar = ['tar', '-x', '--exclude=.wh.*', '-f']

# mount commands
mount = ['mount', '-o', 'bind']
mount_proc = ['mount', '-t', 'proc', '/proc']
mount_sys = ['mount', '-o', 'bind', '/sys']
mount_dev = ['mount', '-o', 'bind', '/dev']
unmount = ['umount']

working_dir = None

# enable host DNS settings
host_dns = ['cp', constants.resolv_path]

# unshare PID within rootfs
unshare_pid = ['unshare', '-pf']

# union mount
union_mount = ['mount', '-t', 'overlay', 'overlay', '-o']

# fuse-overlayfs mount
fuse_mount = ['fuse-overlayfs', '-o']

# global logger
logger = logging.getLogger(constants.logger_name)


def set_working_dir(wd=None):
    '''Set the working/mount directory according to the --working-dir CLI
    option (or lack thereof). This value is used to set the working
    directory properly in get_working_dir().'''
    global working_dir
    working_dir = general.get_top_dir(wd)


def root_command(command, *extra):
    '''Invoke a shell command as root or using sudo. The command is a
    list of shell command words'''
    full_cmd = []
    # add sudo before a command if the user is not root
    if not general.check_root():
        full_cmd.append('sudo')
    full_cmd.extend(command)
    for arg in extra:
        full_cmd.append(arg)
    # invoke
    logger.debug("Running command: %s", ' '.join(full_cmd))
    pipes = subprocess.Popen(full_cmd, stdout=subprocess.PIPE,  # nosec
                             stderr=subprocess.PIPE)
    result, error = pipes.communicate()  # nosec
    if error:
        logger.error("Command failed. %s", error.decode())
        raise subprocess.CalledProcessError(  # nosec
            1, cmd=full_cmd, output=None, stderr=error.decode())
    return result


def shell_command(is_sudo, command, *extra):
    '''Invoke a shell command as a regular user unless explicitly stated.
    This is used to check the result and error message of the command'''
    full_cmd = []
    if not isinstance(is_sudo, bool):
        raise TypeError("First argument should be of type bool")
    if not general.check_root() and is_sudo:
        full_cmd.append('sudo')
    full_cmd.extend(command)
    for arg in extra:
        full_cmd.append(arg)
    # invoke
    logger.debug("Running command: %s", ' '.join(full_cmd))
    pipes = subprocess.Popen(full_cmd, stdout=subprocess.PIPE,  # nosec
                             stderr=subprocess.PIPE)
    return pipes.communicate()  # nosec


def check_tar_permissions(tar_file, directory_path):
    '''Invoke a shell command as the current user. If the error contains
    'Operation not permitted' then return False. Else return True'''
    _, error = shell_command(
        False, extract_tar, tar_file, '-C', directory_path)
    if "Operation not permitted" in error.decode():
        return False
    return True


def check_tar_members(tar_file):
    '''Given the path to the tar file, check to see if there is an error with
    the members of the tarfile or if it is empty'''
    result, error = shell_command(False, check_tar, tar_file)
    if error:
        error_msg = error.decode()
        if "Removing leading" in error_msg:
            pass
        else:
            logger.error("Malformed tar: %s", error_msg)
            raise EOFError("Malformed tarball: {}".format(tar_file))
    return result


def get_working_dir():
    '''General purpose utility to return the absolute path of the working
    directory'''
    return os.path.join(working_dir, constants.temp_folder)


def get_untar_dir(layer_tarfile):
    '''get the directory to untar the layer tar file'''
    return os.path.join(get_working_dir(), os.path.dirname(
        layer_tarfile), constants.untar_dir)


def get_layer_tar_path(layer_tarfile):
    '''get the full path of the layer tar file'''
    return os.path.join(get_working_dir(), layer_tarfile)


def set_up():
    '''Create required directories'''
    op_dir = get_working_dir()
    workdir_path = os.path.join(op_dir, constants.workdir)
    mergedir_path = os.path.join(op_dir, constants.mergedir)
    # create higher level directory
    if not os.path.isdir(op_dir):
        os.mkdir(op_dir)
    # create mount points
    if not os.path.isdir(workdir_path):
        os.mkdir(workdir_path)
    if not os.path.isdir(mergedir_path):
        os.mkdir(mergedir_path)


def extract_tarfile(tar_path, directory_path):
    '''Give the full path to the tar file, extract the tar file into the
    given directory'''
    try:
        os.mkdir(directory_path)
    except FileExistsError:
        # attempt to remove using user permissions
        try:
            shutil.rmtree(directory_path)
            os.mkdir(directory_path)
        except PermissionError:
            # attempt to remove using root permissions
            root_command(remove, directory_path)
            os.mkdir(directory_path)
    # check tarball - should raise an error if anything is wrong
    check_tar_members(tar_path)
    # check if user can extract tarball
    success = check_tar_permissions(tar_path, directory_path)
    if not success:
        # attempt to extract using root permissions
        root_command(extract_tar, tar_path, '-C', directory_path)
        success = True
    return success


def prep_rootfs(rootfs_dir):
    '''Mount required filesystems in the rootfs directory'''
    rootfs_path = os.path.abspath(rootfs_dir)
    proc_path = os.path.join(rootfs_path, 'proc')
    sys_path = os.path.join(rootfs_path, 'sys')
    dev_path = os.path.join(rootfs_path, 'dev')
    if not os.path.exists(proc_path):
        os.mkdir(proc_path)
    if not os.path.exists(sys_path):
        os.mkdir(sys_path)
    if not os.path.exists(dev_path):
        os.mkdir(dev_path)
    try:
        root_command(mount_proc, os.path.join(rootfs_path, 'proc'))
        root_command(mount_sys, os.path.join(rootfs_path, 'sys'))
        root_command(mount_dev, os.path.join(rootfs_path, 'dev'))
        root_command(host_dns, os.path.join(
            rootfs_path, constants.resolv_path[1:]))
    except subprocess.CalledProcessError as error:
        logger.error("%s", error.output)
        raise


def mount_base_layer(base_layer_tar):
    '''To mount to base layer:
        1. Untar the base layer tar file
        2. Mount into mergedir'''
    base_rootfs_path = get_untar_dir(base_layer_tar)
    target_dir_path = os.path.join(get_working_dir(), constants.mergedir)
    root_command(mount, base_rootfs_path, target_dir_path)
    return target_dir_path


def mount_diff_layers(diff_layers_tar, driver=None):
    '''Using overlayfs, mount all the layer tarballs'''
    # make a list of directory paths to give to lowerdir
    lower_dir_paths = []
    for layer_tar in diff_layers_tar:
        lower_dir_paths.append(get_untar_dir(layer_tar))
    upper_dir = lower_dir_paths.pop()
    lower_dir = ':'.join(list(reversed(lower_dir_paths)))
    merge_dir_path = os.path.join(get_working_dir(), constants.mergedir)
    workdir_path = os.path.join(get_working_dir(), constants.workdir)
    args = 'lowerdir=' + lower_dir + ',upperdir=' + upper_dir + \
           ',workdir=' + workdir_path
    if driver == 'fuse':
        root_command(fuse_mount, args, merge_dir_path)
    else:
        root_command(union_mount, args, merge_dir_path)
    return merge_dir_path


def run_chroot_command(command_string, shell):
    '''Run the command string in a chroot jail within the rootfs namespace'''
    target_dir = os.path.join(get_working_dir(), constants.mergedir)
    mount_proc = '--mount-proc=' + os.path.join(
        os.path.abspath(target_dir), 'proc')
    try:
        result = root_command(unshare_pid, mount_proc, 'chroot', target_dir,
                              shell, '-c', command_string)
        return result
    except subprocess.CalledProcessError as e:
        logger.warning("Error executing command in chroot")
        raise subprocess.CalledProcessError(
            1, cmd=command_string, output=None, stderr=e.stderr)


def undo_mount():
    '''Unmount proc, sys, and dev directories'''
    rootfs_path = os.path.join(get_working_dir(), constants.mergedir)
    root_command(unmount, os.path.join(rootfs_path, 'proc'))
    root_command(unmount, os.path.join(rootfs_path, 'sys'))
    root_command(unmount, os.path.join(rootfs_path, 'dev'))


def unmount_rootfs():
    '''Unmount the filesystem'''
    rootfs_path = os.path.join(get_working_dir(), constants.mergedir)
    root_command(unmount, '-rl', rootfs_path)


def clean_up():
    '''Remove all the setup directories'''
    mergedir_path = os.path.join(get_working_dir(), constants.mergedir)
    workdir_path = os.path.join(get_working_dir(), constants.workdir)
    root_command(remove, mergedir_path)
    root_command(remove, workdir_path)


def recover():
    '''Recover after some external error'''
    # try to unmount proc, sys and dev first
    try:
        undo_mount()
    except subprocess.CalledProcessError:
        pass
    try:
        unmount_rootfs()
    except subprocess.CalledProcessError:
        pass
    # clean up the working directory
    clean_up()


def calc_fs_hash(fs_path):
    '''Given the path to the filesystem, calculate the filesystem hash
    We run a shell script located in the tools directory to get the
    file stats and the file content's sha256sum. We then calculate the
    sha256sum of the contents and write the contents in the layer
    directory.
    Note that this file will be deleted if the -k flag is not given'''
    try:
        fs_hash_path = pkg_resources.resource_filename(
            "tern", "tools/fs_hash.sh")
        # required to run in a container natively on Windows
        root_command(["chmod", "+x", fs_hash_path])
        hash_contents = root_command(
            [fs_hash_path], os.path.abspath(fs_path))
        file_name = hashlib.sha256(hash_contents).hexdigest()
        # write file to an appropriate location
        hash_file = os.path.join(os.path.dirname(fs_path), file_name) + '.txt'
        with open(hash_file, 'w') as f:
            f.write(hash_contents.decode('utf-8'))
        return file_name
    except subprocess.CalledProcessError as e:
        raise subprocess.CalledProcessError(  # nosec
            1, cmd=e.cmd, output=e.output, stderr=e.stderr)
