'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging
import os
import subprocess
import yaml

from utils.container import docker_command
from utils.container import execute
from utils.constants import container
from utils import rootfs
from report import errors

'''
Invoking commands in the command library
'''

# base image command library
base_file = 'command_lib/base.yml'
# general snippets in command library
snippet_file = 'command_lib/snippets.yml'
# command library
command_lib = {'base': {}, 'snippets': {}}
with open(os.path.abspath(base_file)) as f:
    command_lib['base'] = yaml.safe_load(f)
with open(os.path.abspath(snippet_file)) as f:
    command_lib['snippets'] = yaml.safe_load(f)
# list of package information keys that the command library can accomodate
base_keys = {'names', 'versions', 'licenses', 'src_urls', 'srcs'}
package_keys = {'name', 'version', 'src_url', 'license', 'src'}

# global logger
logger = logging.getLogger('ternlog')


class FormatAwk(dict):
    '''Code snippets will sometimes use awk and some of the formatting
    syntax resembles python's formatting. This class is meant to override
    the KeyError error that occurs for a missing key when trying to format
    a string such as "awk '{print $1}'"'''
    def __missing__(self, key):
        return '{' + key + '}'


def get_latest_tag(repo):
    '''Given the repo name of the base image, get the latest tag'''
    return command_lib['base'][repo]['latest']


def get_base_listing(base_image, base_tag):
    '''Given the base image and tag, return the listing in the base command
    library'''
    listing = {}
    if base_image in command_lib['base'].keys():
        if base_tag in \
                command_lib['base'][base_image]['tags'].keys():
            listing = \
                command_lib['base'][base_image]['tags'][base_tag]
        if base_tag == 'latest':
            tag = get_latest_tag(base_tag)
            listing = \
                command_lib['base'][base_image]['tags'][tag]
    return listing


def get_command_listing(command_name):
    '''Given a command name retrieve the listing if it exists'''
    listing = {}
    if command_name in command_lib['snippets'].keys():
        listing = command_lib['snippets'][command_name]
    return listing


def check_for_unique_package(package_list, package_name):
    '''In the snippet library the command name has a list of packages that can
    be installed with that command. A package name called 'default' indicates
    that the method of retrieving information applies to any package.
    However if there is an element with a specific name, the default is
    overridden with that name.
    Given a list of package dictionaries, find the package dictionary with the
    given package name. If not there look for a package dictionary with the
    name as 'default'. If that is not there, return an empty dictionary'''
    pkg = {}
    for package in package_list:
        if package['name'] == package_name:
            pkg = package
            break
    if not pkg:
        for package in package_list:
            if package['name'] == 'default':
                pkg = package
                break
    return pkg


def check_library_key(listing, key):
    '''Given the command library listing, check to see if a key is present.
    If the key is in the list of keys that should be in there then provide
    a note'''
    try:
        return listing[key], ''
    except KeyError as e:
        if e in base_keys and e not in package_keys:
            return {}, errors.no_listing_for_base_key.format(
                listing_key=e)
        if e in package_keys and e not in base_keys:
            return {}, errors.no_listing_for_package_key.format(
                listing_key=e)
        return {}, errors.unsupported_listing_for_key.format(listing_key=e)


def get_image_shell(base_image_listing):
    '''Given the base image listing return the image shell. If there is no'''
    shell, msg = check_library_key(base_image_listing, 'shell')
    if not shell:
        shell = ''
    return shell, msg


def get_package_listing(command_name, package_name):
    '''Given a command name, return the package listing from the snippet
    library. First get the listing for the command name and then check if
    there is a package name in the package list or the default'''
    command_listing = get_command_listing(command_name)
    pkg_listing = check_for_unique_package(
        command_listing['packages'], package_name)
    return pkg_listing


def set_command_attrs(command_obj):
    '''Given the command object, move the install and remove listings to
    subcommands and set the flags, then return True. If the command name
    is not in the snippets library then return False'''
    command_listing = get_command_listing(command_obj.name)
    if command_listing:
        # the command is in the library
        if 'install' in command_listing.keys():
            # try to move install to a subcommand
            if command_obj.reassign_word(
                command_listing['install'], 'subcommand'):
                command_obj.set_install()
        if 'remove' in command_listing.keys():
            # try to move remove to a subcommand
            if command_obj.reassign_word(
                command_listing['remove'], 'subcommand'):
                command_obj.set_remove()
        if 'ignore' in command_listing.keys():
            # check if any of the words in the ignore list are in
            # the list of command words
            for ignore_word in command_listing['ignore']:
                if ignore_word in command_obj.words:
                    command_obj.set_ignore()
                    break
        return True
    else:
        return False


def collate_snippets(snippet_list, package=''):
    '''Given a list of snippets, make a concatenated string with all the
    commands'''
    full_cmd = ''
    last_index = len(snippet_list) - 1
    for index in range(0, last_index):
        full_cmd = full_cmd + snippet_list[index].format_map(
            FormatAwk(package=package)) + ' && '
    full_cmd = full_cmd + snippet_list[last_index].format_map(
        FormatAwk(package=package))
    return full_cmd


def invoke_in_container(snippet_list, shell, package='', override=''):
    '''Invoke the commands from the invoke dictionary within a running
    container
    To override the name of the running container pass the name of another
    running container'''
    # construct the full command
    full_cmd = collate_snippets(snippet_list, package)
    try:
        if override:
            result = docker_command(execute, override, shell, '-c', full_cmd)
        else:
            result = docker_command(execute, container, shell, '-c', full_cmd)
        # convert from bytestream to string
        try:
            result = result.decode('utf-8')
        except AttributeError:
            pass
        return result
    except subprocess.CalledProcessError as error:
        logger.warning("Error executing command inside the container")
        raise subprocess.CalledProcessError(
            1, cmd=full_cmd, output=error.output.decode('utf-8'))


def invoke_in_rootfs(snippet_list, shell, package=''):
    '''Invoke the commands from the invoke dictionary in a root filesystem
    assuming the root filesystem is ready to accept commands'''
    # construct the full command
    full_cmd = collate_snippets(snippet_list, package)
    try:
        result = rootfs.run_chroot_command(full_cmd, shell)
        try:
            result = result.decode('utf-8')
        except AttributeError:
            pass
        return result
    except subprocess.CalledProcessError as error:
        logger.warning('Error executing snippets: {0}'.format(error))
        raise


def get_pkg_attr_list(shell, attr_dict, package_name='', override=''):
    '''The command library has package attributes listed like this:
        {invoke: {1: {container: [command1, command2]},
                  2: {host: [command1, command2]}}, delimiter: <delimiter}
    Get the result of the invokes, apply the delimiter to create a list
    override is used for an alternate container name and defaults to
    an empty string'''
    attr_list = []
    error_msgs = ''
    if 'invoke' in attr_dict.keys():
        # invoke the commands
        for step in range(1, len(attr_dict['invoke'].keys()) + 1):
            if 'container' in attr_dict['invoke'][step].keys():
                try:
                    result = invoke_in_container(
                        attr_dict['invoke'][step]['container'], shell,
                        package=package_name, override=override)
                except subprocess.CalledProcessError as error:
                    error_msgs = error_msgs + error.output
                result = result[:-1]
                if 'delimiter' in attr_dict.keys():
                    res_list = result.split(attr_dict['delimiter'])
                    if res_list[-1] == '':
                        res_list.pop()
                    attr_list.extend(res_list)
                else:
                    attr_list.append(result)
    return attr_list, error_msgs


def check_sourcable(command, package_name):
    '''Given a command and package name find out if the sources can be traced
    back. We find this out by checking the package against the command library
    If the package has a url or source retrieval steps associated with it
    then we return True. If not then we return false'''
    sourcable = False
    if command in command_lib['snippets'].keys():
        for package in command_lib['snippets'][command]['packages']:
            if package['name'] == package_name or \
                    package['name'] == 'default':
                if 'url' in package.keys() or \
                        'src' in package.keys():
                    sourcable = True
    return sourcable
