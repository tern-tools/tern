# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
A tool to debug a container image
Specify at what layer you want to debug the container
If the container has only one layer, that is the only option available
"""

import argparse
import os
import subprocess  # nosec
import sys

from tern.utils import rootfs
from tern.utils import constants
from tern.report import report
from tern.analyze.docker import analyze
from tern.analyze.docker import container


def cleanup():
    """Clean up the working directory"""
    rootfs.clean_up()
    rootfs.root_command(rootfs.remove, rootfs.get_working_dir())


def unmount():
    """Go through unmounting the working directory"""
    # try to unmount proc, sys and dev
    try:
        rootfs.undo_mount()
    except subprocess.CalledProcessError:
        pass
    try:
        rootfs.unmount_rootfs()
    except subprocess.CalledProcessError:
        pass


def get_mount_path():
    """Get the path where the filesystem is mounted"""
    return os.path.join(rootfs.get_working_dir(), constants.mergedir)


def check_shell():
    """Check if any shell binary is available in the mounted filesystem"""
    shells = ['/bin/sh', '/bin/bash', '/usr/bin/bash']
    for shell in shells:
        if os.path.exists(os.path.join(get_mount_path(), shell[1:])):
            return shell
    return ''


def drop_into_layer(image_obj, layer_index):
    """Given the image object and the layer index, mount all the layers
    upto the specified layer index and drop into a shell session"""
    rootfs.set_up()
    if layer_index == 0:
        # mount only one layer
        target = rootfs.mount_base_layer(
            image_obj.layers[layer_index].tar_file)
    else:
        # mount all layers uptil the provided layer index
        target = analyze.mount_overlay_fs(image_obj, layer_index)
    # check if there is a shell
    shell = check_shell()
    if shell:
        rootfs.prep_rootfs(target)
        print("Done. Run 'sudo chroot . {}' to look around.".format(shell))
    else:
        print("A shell binary doesn't exist in the filesystem. You're on "
              "your own.")
    print("Working directory is: {}".format(get_mount_path()))
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
        A tool to debug a given container image.
        Give the name of the container image on disk (Eg: golang:alpine)
        and the tool will untar the container image and list out all
        the layers in the image. Then you can pick which layer you
        want to be dropped into''')
    parser.add_argument('--image', metavar='IMAGE',
                        help='Name of image. Eg: docker.io/golang:latest')
    parser.add_argument('--clean', action='store_true',
                        help='Clean up the mounts')
    args = parser.parse_args()
    rootfs.set_working_dir()

    # check if we need to clean
    if args.clean:
        unmount()
        cleanup()
        sys.exit(0)

    # check if the docker is set up properly first
    container.check_docker_setup()

    # first, list all the layers in the image in this format
    # [<layer number>] created_by
    report.setup(image_tag_string=args.image)
    image_obj = report.load_full_image(args.image)
    if image_obj.origins.is_empty():
        # image loading was successful
        # list all the layers
        for layer in image_obj.layers:
            created_by = layer.created_by if layer.created_by else 'unknown'
            print("[{}] {}".format(image_obj.layers.index(layer), created_by))
        try:
            while True:
                try:
                    # input is safe in Python3
                    top_layer = int(input("Pick a layer to debug: "))  # nosec
                except ValueError:
                    print("Not an integer")
                    continue
                if not 0 <= top_layer < len(image_obj.layers):
                    print("Not a valid layer number")
                    continue
                drop_into_layer(image_obj, top_layer)
        except KeyboardInterrupt:
            print("Exiting...")
            cleanup()
    else:
        print("Something when wrong in loading the image")
        cleanup()
