'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging
import subprocess
import sys

from classes.layer import Layer
from classes.package import Package
from command_lib import command_lib as cmds
from utils import cache as cache
from utils import metadata as meta
'''
Common functions
'''

# global logger
logger = logging.getLogger('ternlog')


def get_image_shell(base_image_tag):
    '''Given the base image tag tuple
    (<image>, <tag>) look up the base library for the shell'''
    return cmds.command_lib[
        'base'][base_image_tag[0]]['tags'][base_image_tag[1]]['shell']


def get_base_packages(base_image_tuple, info):
    '''Given a base image and tag tuple, get a list of package objects from
    invoking the commands in the command library base section:
        1. For the image and tag name find if there is a list of package names
        2. If there is an invoke dictionary, invoke the commands
        3. Create a list of packages'''
    pkg_list = []
    # information under the base image tag in the command library
    listing = cmds.get_base_listing(base_image_tuple[0])
    if listing:
        names = cmds.get_pkg_attr_list(info['shell'], info['names'])
        versions = cmds.get_pkg_attr_list(info['shell'], info['versions'])
        licenses = cmds.get_pkg_attr_list(info['shell'], info['licenses'])
        src_urls = cmds.get_pkg_attr_list(info['shell'], info['src_urls'])
        if names and len(names) > 1:
            for index in range(0, len(names)):
                pkg = Package(names[index])
                if len(versions) == len(names):
                    pkg.version = versions[index]
                if len(licenses) == len(names):
                    pkg.license = licenses[index]
                if len(src_urls) == len(names):
                    pkg.src_url = src_urls[index]
                pkg_list.append(pkg)
        else:
            logger.warning(cannot_retrieve_base_packages.format(
                image=base_image_tag[0], tag=base_image_tag[1]))
    else:
        logger.warning(no_image_tag_listing.format(
            image=base_image_tag[0], tag=base_image_tag[1]))
    return pkg_list


def get_base_obj(base_image_tag):
    '''Get a list of layers with their associated packages:
        1. Check if the base image exists on the host machine
        2. Get the layers
        3. For each layer check if there is a list of packages associated
        with it in the cache
        4. If there are no packages return a list of empty layer objects'''
    obj_list = []
    if not check_base_image(base_image_tag):
        # the base image cannot be found locally nor remotely
        # at this point there is no context for Tern to use so raise an
        # exception to exit gracefully
        logger.error(base_image_not_found)
        sys.exit(1)
    else:
        cache.load()
        # get the history with diff ids
        # tuples look like this: (history command, diff_id)
        layer_history = get_layer_history(get_image_tag_string(
            base_image_tag))
        for layer_tuple in layer_history:
            layer_obj = get_layer_obj(layer_tuple[1])
        obj_list.append(layer_obj)
    return obj_list


def get_layer_obj(diff_id):
    '''Given the diff id, retrieve the list of packages from the cache and
    return a layer object'''
    layer_obj = Layer(diff_id)
    packages = cache.get_packages(diff_id)
    for package in packages:
        pkg_obj = Package(package['name'])
        pkg_obj.fill(package)
        layer_obj.add(pkg_obj)
    return layer_obj


def record_layer(layer_obj, package_list=[]):
    '''Given a layer object with a list of packages, record the layer in
    the cache without recording duplicate packages'''
    # get a list of package names in the current layer object
    pkg_names = []
    for pkg in layer_obj.packages:
        pkg_names.append(pkg.name)
    for pkg in package_list:
        if pkg.name not in pkg_names:
            layer_obj.add(pkg)
    cache.add_layer(layer_obj)


def build_layer_obj(sha, pkg_obj_list=[]):
    '''Create a layer object given the sha and a list of package objects'''
    layer_obj = Layer(sha)
    for pkg in pkg_obj_list:
        layer_obj.add(pkg)
    return layer_obj


def save_cache():
    cache.save()


def clear_cache():
    cache.clear()




def get_package_dependencies(command_name, package_name, shell):
    '''Given the command name, the package name and the shell,
    find the list of dependencies'''
    deps = []
    # look up snippet library
    pkg_list = cmds.command_lib['snippets'][command_name]['packages']
    pkg_dict = check_for_unique_package(pkg_list, package_name)
    if pkg_dict and 'deps' in pkg_dict.keys():
        deps.extend(cmds.get_pkg_attr_list(shell, pkg_dict['deps'],
                                           package_name=package_name))
    return list(set(deps))


def get_confirmed_packages(docker_run_inst, shell, prev_pkg_names):
    '''For a dockerfile run instruction which is a tuple of type:
        ('RUN', command)
    1. Get the packages that were installed
    This is in the form of a dictionary that looks like this:
        instruction: <dockerfile instruction>
        recognized: {command_name: [list of installed packages], ...}
        unrecognized: [list of commands in the docker RUN instruction]
    2. Get the dependencies for each of the packages that were installed
    3. Remove dependencies already installed in the previous list of
    package names
    Update the dictionary to move the recognized to confirmed with a
    unique list of packages. The resulting dictionary looks like this:
        instruction: <dockerfile instruction>
        recognized: {command_name: [], ...}
        confirmed: {command_name: [],...}
        unrecognized: [list of commands in the docker RUN instruction]'''
    # get the instruction, the recognized packages and unrecognized commands
    run_dict = cmds.remove_uninstalled(
        cmds.get_packages_per_run(docker_run_inst))
    run_dict.update({'confirmed': {}})
    # get package dependencies
    for cmd in run_dict['recognized'].keys():
        cmd_dict = {cmd: []}
        all_pkgs = []
        remove_pkgs = []
        for pkg in run_dict['recognized'][cmd]:
            deps = get_package_dependencies(cmd, pkg, shell)
            for p in prev_pkg_names:
                if p in deps:
                    deps.remove(p)
            all_pkgs.append(pkg)
            all_pkgs.extend(deps)
            remove_pkgs.append(pkg)
        cmd_dict[cmd].extend(list(set(all_pkgs)))
        run_dict['confirmed'].update(cmd_dict)
        for rem in remove_pkgs:
            run_dict['recognized'][cmd].remove(rem)
    return run_dict


def get_package_obj(command_name, package_name, shell):
    '''Given the command name, and the package name, retrieve the package
    information, create an oject and return the package object'''
    # look up command name in snippet library
    if command_name in cmds.command_lib['snippets'].keys():
        # get the unique or default information
        pkg_list = cmds.command_lib['snippets'][command_name]['packages']
        pkg_info = check_for_unique_package(pkg_list, package_name)
        if pkg_info:
            pkg = Package(package_name)
            # get the information for values
            keys = pkg_info.keys()
            if 'version' in keys:
                try:
                    pkg.version = cmds.get_pkg_attr_list(
                        shell, pkg_info['version'],
                        package_name=package_name)[0]
                except subprocess.CalledProcessError as error:
                    logger.warning(error.output)
            if 'license' in keys:
                try:
                    pkg.license = cmds.get_pkg_attr_list(
                        shell, pkg_info['license'],
                        package_name=package_name)[0]
                except subprocess.CalledProcessError as error:
                    logger.warning(error.output)
            if 'src_url' in keys:
                try:
                    pkg.src_url = cmds.get_pkg_attr_list(
                        shell, pkg_info['src_url'],
                        package_name=package_name)[0]
                except subprocess.CalledProcessError as error:
                    logger.warning(error.output)
            return pkg
        else:
            print(
                'No package named {} nor default listing'.format(package_name))
    else:
        print('No command {} listed in snippet library'.format(command_name))


def get_packages_from_snippets(command_dict, shell):
    '''Command dictionary looks like this:
        { command: [list of packages], command: [list of packages]...}
    This is the result of parsing through a Dockerfile RUN command.
    Return a list of packages objects that are installed from the Dockerfile
    RUN command'''
    package_list = []
    for cmd in command_dict.keys():
        for pkg in command_dict[cmd]:
            pkg_obj = get_package_obj(cmd, pkg, shell)
            package_list.append(pkg_obj)
    return package_list


def get_layer_history(image_tag_string):
    '''For an available image, get a list of tuples containing the dockerfile
    instruction that created the layer and the diff id of that layer'''
    history_list = []
    # save the image first
    if not cmds.extract_image_metadata(image_tag_string):
        # there was some error in extracting the metadata so we cannot
        # find the context for the base image
        print(cannot_extract_base_image)
        raise
    else:
        # get the list of non-empty history
        config = meta.get_image_config()
        history = meta.get_nonempty_history(config)
        diff_ids = meta.get_diff_ids(config)
        # create a list of tuples
        for index in range(0, len(history)):
            history_list.append((history[index], diff_ids[index]))
    return history_list


def collate_package_names(pkg_name_list, layer_obj):
    '''Given a list of package names or an empty list. Append packages from
    the layer object and return the new list.
    Use this to keep track of packages introduced in the layers before
    so the subsequent layers do not have the same packages.'''
    for pkg in layer_obj.get_package_names():
        pkg_name_list.append(pkg)
