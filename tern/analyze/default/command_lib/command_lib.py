# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Invoking commands in the command library
"""

import logging
import os
import yaml
import copy
import pkg_resources

from tern.utils import constants
from tern.report import errors


# base image command library
base_file = pkg_resources.resource_filename(
    'tern', 'analyze/default/command_lib/base.yml')
# general snippets in command library
snippet_file = pkg_resources.resource_filename(
    'tern', 'analyze/default/command_lib/snippets.yml')
# common information
common_file = pkg_resources.resource_filename(
    'tern', 'analyze/default/command_lib/common.yml')

# command library
command_lib = {'common': {}, 'base': {}, 'snippets': {}}
with open(os.path.abspath(common_file)) as f:
    command_lib['common'] = yaml.safe_load(f)
with open(os.path.abspath(base_file)) as f:
    command_lib['base'] = yaml.safe_load(f)
with open(os.path.abspath(snippet_file)) as f:
    command_lib['snippets'] = yaml.safe_load(f)
# list of package information keys that the command library can accomodate
base_keys = {'names', 'versions', 'licenses', 'copyrights', 'proj_urls',
             'srcs', 'files'}
package_keys = {'name', 'version', 'license', 'copyright', 'proj_url', 'src',
                'files'}

# global logger
logger = logging.getLogger(constants.logger_name)


class FormatAwk(dict):
    '''Code snippets will sometimes use awk and some of the formatting
    syntax resembles python's formatting. This class is meant to override
    the KeyError error that occurs for a missing key when trying to format
    a string such as "awk '{print $1}'"'''
    def __missing__(self, key):
        return '{' + key + '}'


def get_base_listing(key):
    '''Given the key listing in base.yml, return the dictionary'''
    listing = {}
    if key in command_lib['base'].keys():
        listing = copy.deepcopy(command_lib['base'][key])
    else:
        logger.warning("%s", errors.no_listing_for_base_key.format(
            listing_key=key))
    return listing


def get_command_listing(command_name):
    '''Given a command name retrieve the listing if it exists'''
    listing = {}
    if command_name in command_lib['snippets'].keys():
        listing = command_lib['snippets'][command_name]
    else:
        logger.warning("%s", errors.no_listing_for_snippet_key.format(
            listing_key=command_name))
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


def get_package_listing(command_name):
    '''Given a command name, return the package listing from the snippet
    library.'''
    return get_command_listing(command_name)['packages']


def set_subcommand(command_obj, subcommand_type, subcommand_words):
    """This subroutine will check to see if subcommand_words can be reassigned
    as a subcommand. If it can, then set the command as the subcommand_type.
    If not, then do not set the command_obj as anything. subcommand_type can
    be 'install', 'remove' or 'ignore'"""
    for word in subcommand_words:
        if command_obj.reassign_word(word, 'subcommand'):
            if subcommand_type == 'install':
                command_obj.set_install()
            elif subcommand_type == 'remove':
                command_obj.set_remove()
            else:
                command_obj.set_ignore()
            return True
    return False


def set_command_attrs(command_obj):
    '''Given the command object, move the install and remove listings to
    subcommands and set the flags, then return True. If the command name
    is not in the snippets library then return False'''
    command_listing = get_command_listing(command_obj.name)
    if command_listing:
        # the command is in the library
        # look for install, remove and ignore commands
        if 'install' in command_listing.keys():
            set_subcommand(command_obj, 'install', command_listing['install'])
        if 'remove' in command_listing.keys():
            set_subcommand(command_obj, 'remove', command_listing['remove'])
        if 'ignore' in command_listing.keys():
            # check if any of the words in the ignore list are in
            set_subcommand(command_obj, 'ignore', command_listing['ignore'])
        return True
    return False


def collate_snippets(snippet_list, package=''):
    '''Given a list of snippets, make a concatenated string with all the
    commands'''
    # Escape any braces that might confuse Python formatting
    for i, snip in enumerate(snippet_list):
        if '{}' in snip:
            snippet_list[i] = snip.replace('{}', '{{}}')
    full_cmd = ''
    last_index = len(snippet_list) - 1
    for index in range(0, last_index):
        full_cmd = full_cmd + snippet_list[index].format_map(
            FormatAwk(package=package)) + ' && '
    full_cmd = full_cmd + snippet_list[last_index].format_map(
        FormatAwk(package=package))
    return full_cmd


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


def check_pkg_format(binary):
    '''Given a binary package manager, return the associated pkg_format from
    base.yml. If the binary is not valid in base.yml, return an empty
    string.'''
    try:
        return command_lib['base'][binary]['pkg_format']
    except KeyError:
        return ''


def check_os_guess(binary):
    '''Given a binary package manager, return the associated os_guess from
    base.yml. If the binary is not valid in base.yml, return an empty
    string.'''
    os_list = []
    try:
        for o in command_lib['base'][binary]['os_guess']:
            os_list.append(o)
        return ', '.join(os_list)
    except KeyError:
        return ''


def check_pinning_separator(command_name):
    '''Given command name, look up the name in snippets.yml and find the
    corresponding package manager's pinning separator'''
    pkg_listing = get_package_listing(command_name)
    if isinstance(pkg_listing, str):
        try:
            return command_lib['base'][pkg_listing]['pinning_separator']
        except KeyError:
            return ''
    return ''
