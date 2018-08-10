'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''
import hashlib
import logging
import os
import stat
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
        2. Mount into mergedir'''
    base_rootfs_path = get_untar_dir(base_layer_tar)
    source_dir_path = os.path.join(constants.temp_folder, base_layer_tar)
    target_dir_path = os.path.join(constants.temp_folder, constants.mergedir)
    if os.path.isdir(base_rootfs_path):
        root_command(remove, base_rootfs_path)
    extract_layer_tar(source_dir_path, base_rootfs_path)
    root_command(mount, base_rootfs_path, target_dir_path)
    return target_dir_path


def mount_diff_layer(diff_layer_tar):
    '''To mount the diff layer:
        1. Untar the diff rootfs
        2. Union mount this directory on the mergedir'''
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
    return merge_dir_path


def run_chroot_command(command_string, shell):
    '''Run the command string in a chroot jail within the rootfs namespace'''
    target_dir = os.path.join(constants.temp_folder, constants.mergedir)
    mount_proc = '--mount-proc=' + os.path.join(
        os.path.abspath(target_dir), 'proc')
    try:
        result = root_command(unshare_pid, mount_proc, 'chroot', target_dir,
                              shell, '-c', command_string)
        return result
    except subprocess.CalledProcessError as error:
        logger.warning("Error executing command in chroot")
        raise subprocess.CalledProcessError(
            1, cmd=command_string, output=error.output.decode('utf-8'))


def undo_mount():
    '''Unmount proc, sys, and dev directories'''
    rootfs_path = os.path.join(constants.temp_folder, constants.mergedir)
    root_command(unmount, os.path.join(rootfs_path, 'proc'))
    root_command(unmount, os.path.join(rootfs_path, 'sys'))
    root_command(unmount, os.path.join(rootfs_path, 'dev'))


def unmount_rootfs(num_layers):
    '''Unmount the overlay filesystem'''
    rootfs_path = os.path.join(constants.temp_folder, constants.mergedir)
    for _ in range(num_layers):
        root_command(unmount, '-rl', rootfs_path)


def clean_up():
    '''Remove all the setup directories'''
    mergedir_path = os.path.join(constants.temp_folder, constants.mergedir)
    workdir_path = os.path.join(constants.temp_folder, constants.workdir)
    root_command(remove, mergedir_path)
    root_command(remove, workdir_path)


def get_file_stats(workdir, file_path):
    '''Given the working directory path and path to a file, return a string
    with the file stats in this form:
        filepath|inode|file permissions|uid|gid|size|num links|extended
        attributes|
    List the extended attributes as a key-value pair and a comma delimiter'''
    # find the extended attributes for the file
    attrs_list = []
    for attr in os.listxattr(file_path):
        attr_value = os.getxattr(file_path, attr).decode(
            'utf-8').strip(' \t\r\b\0')
        attr_str = attr + "=" + attr_value
        attrs_list.append(attr_str)
    attrs = ','.join(attrs_list)
    # get file status
    stats = os.stat(file_path)
    perms = stat.filemode(stats.st_mode)
    # get file path without the working directory
    file_from_root = file_path.split(workdir).pop()
    file_stats = file_from_root + '|' + str(stats.st_ino) + '|' + perms + \
        '|' + str(stats.st_uid) + '|' + str(stats.st_gid) + '|' + \
        str(stats.st_size) + '|' + str(stats.st_nlink) + '|' + attrs + '|'
    return file_stats


def get_file_sha(file_path):
    '''Given the path to a file, return the sha256sum of the file'''
    sha256sum = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for file_bytes in iter(lambda: f.read(4096), b""):
            sha256sum.update(file_bytes)
    return sha256sum.hexdigest()


def calc_fs_hash(fs_path):
    '''Given the path to the filesystem, calculate the filesystem hash as
    follows:
        1. For each file in the fs_path, find file statistics
        2. Append the file content's 256sha hash to the file stats
        3. Calculate the sha of the contents
        4. Save this file in the layer sha's directory to look at later
        Note that this file will be deleted if the -k flag is not given'''
    file_list = []
    for root, _, files in os.walk(fs_path, topdown=True, onerror=None):
        for f_name in files:
            file_path = os.path.join(root, f_name)
            file_desc = get_file_stats(fs_path, file_path)
            file_desc = file_desc + get_file_sha(file_path)
            file_list.append(file_desc)
    hash_contents = '\n'.join(file_list)
    file_name = hashlib.sha256(hash_contents.encode('utf-8')).hexdigest()
    # write file to an appropriate location
    hash_file = os.path.join(os.path.dirname(fs_path), file_name) + '.txt'
    with open(hash_file, 'w') as f:
        f.write(hash_contents)
    return file_name
