'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging
import subprocess

from classes.package import Package
from classes.notice import Notice
from command_lib import command_lib as cmdlib
from report import info
from report import errors
from utils import cache as cache
from utils import metadata as meta
from utils import constants as const
from utils.container import check_container
'''
Common functions
'''

# global logger
logger = logging.getLogger('ternlog')


def load_from_cache(image):
    '''Given an image object, check against cache to see if a layer id exists
    if yes then get the package list and load it in the image layer. If it
    doesn't exist continue. If not all the layers have packages, return False
    else return True'''
    is_full = True
    for layer in image.layers:
        if not layer.packages:
            raw_pkg_list = cache.get_packages(layer.id)
            if not raw_pkg_list:
                is_full = False
            else:
                from_cache_notice = Notice()
                from_cache_notice.origin = image.get_image_option() + \
                    layer.id
                from_cache_notice.message = info.loading_from_cache.format(
                    layer_id=layer.id)
                from_cache_notice.level = 'info'
                layer.add_notice(from_cache_notice)
                for pkg_dict in raw_pkg_list:
                    pkg = Package(pkg_dict['name'])
                    pkg.fill(pkg_dict)
                    layer.add_package(pkg)
    return image, is_full


def add_base_packages(image, info):
    '''Given an image object, get a list of package objects from
    invoking the commands in the command library base section:
        1. For the image and tag name find if there is a list of package names
        2. If there is an invoke dictionary, invoke the commands
        3. Create a list of packages
        4. Add them to the image'''
    # information under the base image tag in the command library
    listing = cmdlib.get_base_listing(image.name, image.tag)
    origin = 'command_lib/base.yml'
    if listing:
        shell, msg = cmdlib.get_image_shell(listing)
        if not shell:
            # add a warning notice for no shell in the command library
            no_shell_message = errors.no_shell_listing.format(
                image_name=image.name, image_tag=image.tag,
                default_shell=const.shell)
            no_shell_notice = Notice(origin, no_shell_message, 'warning')
            image.add_notice(no_shell_notice)
            # add a hint notice to add the shell to the command library
            add_shell_message = errors.no_listing_for_base_key.format(
                listing_key='shell')
            add_shell_notice = Notice(origin, add_shell_message, 'hint')
            image.add_notice(add_shell_notice)
            shell = const.shell
        # check if a container is running first
        # eventually this needs to change to use derivatives that have
        # more than 1 layer
        # for now, we add the list of packages to all the layers in a
        # starting base image
        if check_container():
            names, n_msg = cmdlib.get_pkg_attr_list(shell, info['names'])
            versions, v_msg = cmdlib.get_pkg_attr_list(shell, info['versions'])
            licenses, l_msg = cmdlib.get_pkg_attr_list(shell, info['licenses'])
            src_urls, u_msg = cmdlib.get_pkg_attr_list(shell, info['src_urls'])
            # add a notice to the image if something went wrong
            invoke_msg = n_msg + v_msg + l_msg + u_msg
            if invoke_msg:
                pkg_invoke_notice = Notice(origin, invoke_msg, 'error')
                image.add_notice(pkg_invoke_notice)
            if names and len(names) > 1:
                for index in range(0, len(names)):
                    pkg = Package(names[index])
                    if len(versions) == len(names):
                        pkg.version = versions[index]
                    if len(licenses) == len(names):
                        pkg.license = licenses[index]
                    if len(src_urls) == len(names):
                        pkg.src_url = src_urls[index]
                        for layer in image.layers:
                            layer.add_package(pkg)
            # add all the packages to the cache
            for layer in image.layers:
                cache.add_layer(layer)
        # if no container is running give a logging error
        else:
            logger.error(errors.no_running_docker_container)
    # if there is no listing add a notice
    else:
        no_listing_notice = Notice(origin, errors.no_image_tag_listing.format(
            image_name=image.name, image_tag=image.tag), 'error')
        image.add_notice(no_listing_notice)


def fill_package_metadata(pkg_obj, pkg_listing, shell):
    '''Given a Package object and the Package listing from the command
    library, fill in the attribute value returned from looking up the
    data and methods of the package listing.
    Fill out: version, license and src_url
    If there are errors, fill out notices'''
    origin = 'command_lib/snippets.yml'
    # version
    version_listing, listing_msg = cmdlib.check_library_key(
        pkg_listing, 'version')
    if version_listing:
        version_list, invoke_msg = cmdlib.get_pkg_attr_list(
            shell, version_listing, package_name=pkg_obj.name)
        if version_list:
            pkg_obj.version = version_list[0]
        else:
            version_invoke_error_notice = Notice(origin, invoke_msg, 'error')
            pkg_obj.add_notice(version_invoke_error_notice)
    else:
        no_version_listing_notice = Notice(origin, listing_msg, 'warning')
        pkg_obj.add_notice(no_version_listing_notice)
    # license
    license_listing, listing_msg = cmdlib.check_library_key(
        pkg_listing, 'license')
    if license_listing:
        license_list, invoke_msg = cmdlib.get_pkg_attr_list(
            shell, license_listing, package_name=pkg_obj.name)
        if license_list:
            pkg_obj.license = license_list[0]
        else:
            license_invoke_error_notice = Notice(origin, invoke_msg, 'error')
            pkg_obj.add_notice(license_invoke_error_notice)
    else:
        no_license_listing_notice = Notice(origin, listing_msg, 'warning')
        pkg_obj.add_notice(no_license_listing_notice)
    # src_urls
    url_listing, listing_msg = cmdlib.check_library_key(
        pkg_listing, 'license')
    if url_listing:
        url_list, invoke_msg = cmdlib.get_pkg_attr_list(
            shell, url_listing, package_name=pkg_obj.name)
        if url_list:
            pkg_obj.src_url = url_list[0]
        else:
            url_invoke_error_notice = Notice(origin, invoke_msg, 'error')
            pkg_obj.add_notice(url_invoke_error_notice)
    else:
        no_url_listing_notice = Notice(origin, listing_msg, 'warning')
        pkg_obj.add_notice(no_url_listing_notice)


def get_package_obj(command_name, package_name, shell):
    '''Given the command name, and the package name, retrieve the package
    information, create an oject and return the package object'''
    listing = cmdlib.get_command_listing(command_name)
    if listing:
        # get the unique or default information
        pkg_info = cmdlib.check_for_unique_package(
            listing['packages'], package_name)
        if pkg_info:
            pkg = Package(package_name)
            fill_package_metadata(pkg, pkg_info, shell)
            return pkg, ''
        else:
            return None, errors.no_command_listing.format(
                command_name=command_name)

    else:
        return None, errors.no_listing_for_snippet_key

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
