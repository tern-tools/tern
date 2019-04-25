# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Test script for running commands in a chroot environment to check if the
results produced are expected
"""

import argparse
import subprocess  # nosec

from tern.command_lib import command_lib
from tern.utils import rootfs
from tern.report import report


def look_up_lib(keys):
    '''Return the dictionary for the keys given
    Assuming that the keys go in order.
    Eg: 'snippets', then 'command name', then 'packages'''
    subd = command_lib.command_lib[keys.pop(0)]
    while keys:
        subd = subd[keys.pop(0)]
    return subd


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
        A script to test if the set of commands that get executed within
        a chroot environment produce expected results.
        In order to use this, an image should already exist on disk''')
    parser.add_argument('--image',
                        help='Name of image. Eg: docker.io/golang:latest')
    parser.add_argument('--keys', nargs='+',
                        help='List of keys to look up in the command '
                        'library. Eg: base dpkg names')
    parser.add_argument('--shell', default='/bin/sh',
                        help='The shell executable that the image uses')
    parser.add_argument('--package', default='',
                        help='A package name that the command needs to '
                        'execute with. Useful when testing commands in the '
                        'snippet library')
    args = parser.parse_args()

    # first, mount all the layers in the image
    report.setup(image_tag_string=args.image)
    image_obj = report.load_full_image(args.image)
    if image_obj.origins.is_empty():
        # image loading was successful
        # proceed mounting diff filesystems
        if len(image_obj.layers) == 1:
            # mount only one layer
            target = rootfs.mount_base_layer(image_obj.layers[0].tar_file)
            rootfs.prep_rootfs(target)
        else:
            report.mount_overlay_fs(image_obj, len(image_obj.layers) - 1)
        # invoke commands in chroot
        # if we're looking up the snippets library
        # we should see 'snippets' in the keys
        if 'snippets' in args.keys and 'packages' in args.keys:
            # get the package info that corresponds to the package name
            # or get the default
            last = args.keys.pop()
            info_list = look_up_lib(args.keys)
            info_dict = command_lib.check_for_unique_package(
                info_list, args.package)[last]
        else:
            info_dict = look_up_lib(args.keys)
        # try to invoke the commands
        try:
            result = command_lib.get_pkg_attr_list(
                args.shell, info_dict, args.package)
            print('Output list: ' + ' '.join(result[0]))
            print('Error messages: ' + result[1])
            print('Number of elements: ' + str(len(result[0])))
        except subprocess.CalledProcessError as error:
            print(error.output)
        # undo the mounts
        rootfs.undo_mount()
        rootfs.unmount_rootfs()
    else:
        print("Something when wrong in loading the image")
    report.teardown()
    report.clean_image_tars(image_obj)
    report.clean_working_dir(False)
