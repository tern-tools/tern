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
from utils.general import parse_command
from utils.constants import container
from classes.command import Command
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


def get_shell_commands(run_comm):
    '''Given a RUN command return a list of shell commands to be run'''
    comm_list = run_comm.split('&&')
    cleaned_list = []
    for comm in comm_list:
        cleaned_list.append(Command(comm.strip()))
    return cleaned_list


def get_latest_tag(repo):
    '''Given the repo name of the base image, get the latest tag'''
    return command_lib['base'][repo]['latest']


def get_base_listing(image_tuple):
    '''Given the base image tag tuple, return the listing in the base command
    library'''
    listing = {}
    if image_tuple[0] in command_lib['base'].keys():
        if image_tuple[1] in \
                command_lib['base'][image_tuple[0]]['tags'].keys():
            listing = \
                command_lib['base'][image_tuple[0]]['tags'][image_tuple[1]]
        if image_tuple[1] == 'latest':
            tag = get_latest_tag(image_tuple[0])
            listing = \
                command_lib['base'][image_tuple[0]]['tags'][tag]
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
    given package name. If not there look for a pacakge dictionary with the
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


def set_command_attrs(command_obj):
    '''Given the command object, move the install and remove listings to
    subcommands and set the flags, then return True. If the command name
    is not in the snippets library then return False'''
    command_listing = get_command_listing(command_obj.name)
    if command_listing:
        # the command is in the library
        if 'install' in command_listing.keys():
            # try to move install to a subcommand
            if command_obj(command_listing['install'], 'subcommand'):
                command_obj.set_install()
        if 'remove' in command_listing.keys():
            # try to move remove to a subcommand
            if command_obj(command_listing['remove'], 'subcommand'):
                command_obj.set_remove()
        if 'ignore' in command_listing.keys():
            # check if any of the words in the ignore list are in
            # the list of command words
            for ignore_word in command_listing['ignore']:
                if ignore_word in command_obj.words:
                    command_obj.set_ignore()
                    break


def get_packages_per_run(docker_run_command):
    '''Given a Docker RUN instruction retrieve a dictionary of recognized
    and unrecognized commands
    the dictionary should look like this:
        instruction: <dockerfile instruction>
        recognized: { <command name>:
                         {installed: [list of packages installed]
                          removed: [list of packaged removed]},...}
        unrecognized: [list shell commands that were not recognized]'''
    docker_inst = docker_run_command[0] + ' ' + docker_run_command[1]
    pkg_dict = {'instruction': docker_inst,
                'recognized': {},
                'unrecognized': []}
    shell_commands = get_shell_commands(docker_run_command[1])
    for command in shell_commands:
        installed_dict = {'installed': [], 'removed': []}
        command_obj = parse_command(command)
        # see if command is in the snippet library
        name = command_obj['name']
        sub = command_obj['subcommand']
        if name in command_lib['snippets'].keys():
            is_package_op = False
            if sub == command_lib['snippets'][name]['install']:
                is_package_op = True
                installed_dict['installed'] = command_obj['arguments']
            if sub == command_lib['snippets'][name]['remove']:
                is_package_op = True
                installed_dict['removed'] = command_obj['arguments']
            # add only if there are some packages installed or removed
            if is_package_op:
                pkg_dict['recognized'].update({name: installed_dict})
        else:
            pkg_dict['unrecognized'].append(command)
    return pkg_dict


def get_package_listing(docker_instructions):
    '''Given the docker instructions in a dockerfile,  get a dictionary of
    packages that are in the command library of retrievable sources
    If it does not exist in the library then record them under
    unrecognized commands
    the dict looks like this:
        recognized:{ <command name>:
                        {installed: [list of packages installed],
                        removed: [list of packages removed]}}
        unrecognized: [list of shell commands that were not recognized]
    '''
    pkg_dict = {'recognized': {}, 'unrecognized': []}
    shell_commands = []
    for instr in docker_instructions:
        if instr[0] == 'RUN':
            shell_commands.extend(get_shell_commands(instr[1]))
    for command in shell_commands:
        installed_dict = {'installed': [], 'removed': []}
        command_obj = parse_command(command)
        # see if command is in the snippet library
        name = command_obj['name']
        sub = command_obj['subcommand']
        if name in command_lib['snippets'].keys():
            is_package_op = False
            if sub == command_lib['snippets'][name]['install']:
                is_package_op = True
                installed_dict['installed'] = command_obj['arguments']
            if sub == command_lib['snippets'][name]['remove']:
                is_package_op = True
                installed_dict['removed'] = command_obj['arguments']
            # add only if there are some packages installed or removed
            if is_package_op:
                pkg_dict['recognized'].update({name: installed_dict})
        else:
            pkg_dict['unrecognized'].append(command)
    return pkg_dict


def remove_uninstalled(pkg_dict):
    '''Given a dictionary containing the package listing for a set of
    docker commands, return an updated dictionary with only the packages that
    are installed
    The resulting dictionary should look like this:
        recognized:{ {<command name>: [list of packages installed]},...}
        unrecognized: [list of shell commands that were not recognized]
        '''
    for command in pkg_dict['recognized'].keys():
        installed_list = pkg_dict['recognized'][command]['installed']
        remove_list = pkg_dict['recognized'][command]['removed']
        for remove in remove_list:
            if remove in installed_list:
                installed_list.remove(remove)
        pkg_dict['recognized'].update({command: installed_list})
    return pkg_dict


def invoke_in_container(snippet_list, shell, package='', override=''):
    '''Invoke the commands from the invoke dictionary within a running
    container
    To override the name of the running container pass the name of another
    running container'''
    # construct the full command
    full_cmd = ''
    last_index = len(snippet_list) - 1
    for index in range(0, last_index):
        full_cmd = full_cmd + snippet_list[index].format_map(
            FormatAwk(package=package)) + ' && '
    full_cmd = full_cmd + snippet_list[last_index].format_map(
        FormatAwk(package=package))
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


def get_pkg_attr_list(shell, attr_dict, package_name='', override=''):
    '''The command library has package attributes listed like this:
        {invoke: {1: {container: [command1, command2]},
                  2: {host: [command1, command2]}}, delimiter: <delimiter}
    Get the result of the invokes, apply the delimiter to create a list
    override is used for an alternate container name and defaults to
    an empty string'''
    attr_list = []
    if 'invoke' in attr_dict.keys():
        # invoke the commands
        for step in range(1, len(attr_dict['invoke'].keys()) + 1):
            if 'container' in attr_dict['invoke'][step].keys():
                try:
                    result = invoke_in_container(
                        attr_dict['invoke'][step]['container'], shell,
                        package=package_name, override=override)
                except subprocess.CalledProcessError as error:
                    raise subprocess.CalledProcessError(
                        1, cmd=error.cmd, output=error.output)
                result = result[:-1]
                if 'delimiter' in attr_dict.keys():
                    res_list = result.split(attr_dict['delimiter'])
                    if res_list[-1] == '':
                        res_list.pop()
                    attr_list.extend(res_list)
                else:
                    attr_list.append(result)
    return attr_list


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
