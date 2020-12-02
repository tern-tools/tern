# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Execution paths for "debugging" tern with a container image
This is meant to be used when checking tern's operation
We currently have the following options:
    - Look at what the command library scripts are doing when they get executed
      in a chroot environment on a mounted overlay filesystem
"""
from tern import prep
from tern.utils import rootfs
from tern.analyze.default.command_lib import command_lib
from tern.analyze.default import collect
from tern.analyze.default.container import run
from tern.analyze.default.container import image as cimage
from tern.analyze.default.container import single_layer
from tern.analyze.default.container import multi_layer


def mount_container_image(image_obj, driver=None):
    """Mount the container image to make it ready to invoke scripts"""
    if len(image_obj.layers) > 1:
        target = multi_layer.mount_overlay_fs(
            image_obj, len(image_obj.layers) - 1, driver)
        rootfs.prep_rootfs(target)
    else:
        single_layer.mount_first_layer(image_obj.layers[0])


def look_up_lib(keys):
    '''Return the dictionary for the keys given
    Assuming that the keys go in order.
    Eg: 'snippets', then 'command name', then 'packages'''
    subd = command_lib.command_lib[keys.pop(0)]
    while keys:
        subd = subd[keys.pop(0)]
    return subd


def invoke_script(args):
    """Assuming we have a mounted filesystem, invoke the script in the
    command library"""
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
    result = collect.get_pkg_attrs(
        info_dict, args.shell, package_name=args.package)
    print()
    print("*************************************************************")
    print("          Command Library Script Verification mode           ")
    print("*************************************************************")
    print()
    print('Output list: ' + ' '.join(result[0]))
    print('Error messages: ' + result[1])
    print('Number of elements: ' + str(len(result[0])))
    print()


def execute_invoke(args):
    """Execution path for checking command library scripts"""
    # do the initial setup
    # this should be the same as the full container image extraction and
    # loading
    image_string = run.extract_image(args)
    if image_string:
        full_image = cimage.load_full_image(image_string)
        if full_image.origins.is_empty():
            run.setup(full_image)
            # we now mount the whole container image
            mount_container_image(full_image, args.driver)
            # invoke commands in chroot
            invoke_script(args)
            # undo the mounts
            rootfs.undo_mount()
            rootfs.unmount_rootfs()
            # cleanup
            rootfs.clean_up()
    else:
        print("Something when wrong in loading the image")
    if not args.keep_wd:
        prep.clean_image_tars(full_image)


def execute_debug(args):
    """Debug container images"""
    if args.docker_image and args.keys:
        # we have an image to mount and some scripts to invoke
        execute_invoke(args)
