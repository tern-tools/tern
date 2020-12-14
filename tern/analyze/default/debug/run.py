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
import os
import subprocess  # nosec
import sys

from tern import prep
from tern.utils import rootfs
from tern.utils import constants
from tern.analyze.default.command_lib import command_lib
from tern.analyze.default import collect
from tern.analyze.default.container import run
from tern.analyze.default.container import image as cimage
from tern.analyze.default.container import single_layer
from tern.analyze.default.container import multi_layer


def check_image_obj(image_string):
    """Return the image object and if it was loaded successfully"""
    if image_string:
        full_image = cimage.load_full_image(image_string)
        if full_image.origins.is_empty():
            return full_image, True
        print("Something went wrong in loading the image")
        return None, False
    print("Something went wrong in extracting the image")
    return None, False


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


def get_mount_path():
    """Get the path where the filesystem is mounted"""
    return os.path.join(rootfs.get_working_dir(), constants.mergedir)


def check_shell():
    """Check if any shell binary is available in the mounted filesystem"""
    for shell in command_lib.command_lib['common']['shells']:
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
        target = multi_layer.mount_overlay_fs(image_obj, layer_index)
    mount_path = get_mount_path()
    print("\nWorking directory is: {}\n".format(mount_path))
    # check if there is a shell
    shell = check_shell()
    if shell:
        rootfs.prep_rootfs(target)
        print("\nRun 'cd {} && sudo chroot . {}' to look around".format(
            mount_path, shell))
    else:
        print("\nRun 'cd {}' to look around".format(mount_path))
        print("A shell binary doesn't exist in the filesystem. You're on "
              "your own.")
    print("\nAfter exiting from your session, run 'cd -' to go back "
          "and 'tern debug --recover' to clean up.\n")
    sys.exit(0)


def execute_invoke(image_obj, args):
    """Execution path for checking command library scripts"""
    # we set up the image for analysis
    run.setup(image_obj)
    # we now mount the whole container image
    mount_container_image(image_obj, args.driver)
    # invoke commands in chroot
    invoke_script(args)
    # undo the mounts
    rootfs.undo_mount()
    rootfs.unmount_rootfs()
    # cleanup
    rootfs.clean_up()
    if not args.keep_wd:
        prep.clean_image_tars(image_obj)


def execute_step(image_obj, args):
    """Execution path for looking at a container image filesystem at a
    specific layer. This is an interactive debugging option and should not be
    used in production."""
    print()
    print("*************************************************************")
    print("          Container Image Interactive Debug Mode             ")
    print("*************************************************************")
    print()
    for layer in image_obj.layers:
        created_by = layer.created_by if layer.created_by else 'unknown'
        print("[{}] {}".format(image_obj.layers.index(layer), created_by))
    try:
        while True:
            try:
                # input is safe in Python3
                top_layer = int(input("\nPick a layer to debug: "))  # nosec
            except ValueError:
                print("Not an integer")
                continue
            if not 0 <= top_layer < len(image_obj.layers):
                print("Not a valid layer number")
                continue
            drop_into_layer(image_obj, top_layer)
    except KeyboardInterrupt:
        print("Exiting...")
        rootfs.clean_up()
    if not args.keep_wd:
        prep.clean_image_tars(image_obj)


def recover():
    """Undo all the mounts and clean up directories"""
    try:
        rootfs.undo_mount()
    except subprocess.CalledProcessError:
        pass
    try:
        rootfs.unmount_rootfs()
    except subprocess.CalledProcessError:
        pass
    # we nuke all the directories after mounting
    rootfs.clean_up()
    working_dir = rootfs.get_working_dir()
    if os.path.exists(working_dir):
        rootfs.root_command(rootfs.remove, working_dir)


def execute_debug(args):
    """Debug container images"""
    if args.docker_image:
        image_string = run.extract_image(args)
        full_image, success = check_image_obj(image_string)
        if success:
            if args.keys:
                # we have an image to mount and some scripts to invoke
                execute_invoke(full_image, args)
            elif args.step:
                # we need to step into a layer state in a container image
                execute_step(full_image, args)
    elif args.recover:
        # we need to recover the filesystem
        recover()
    else:
        print("Debug mode: nothing to do")
