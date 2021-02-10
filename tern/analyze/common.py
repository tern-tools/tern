# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

'''
Common functions
'''

import logging
import os
import subprocess  # nosec

from tern.classes.notice import Notice
from tern.classes.package import Package
from tern.classes.file_data import FileData
from tern.classes.command import Command
from tern.utils import cache
from tern.utils import constants
from tern.utils import general
from tern.utils import rootfs
from debut import debcon
from debut import copyright as debut_copyright

# global logger
logger = logging.getLogger(constants.logger_name)


def get_shell_commands(shell_command_line):
    '''Given a shell command line, get a list of Command objects and report on
    branch statements'''
    statements = general.split_command(shell_command_line)
    command_list = []
    branch_report = ''
    # traverse the statements, pick out the loop and commands.
    for stat in statements:
        if 'command' in stat:
            command_list.append(Command(stat['command']))
        elif 'loop' in stat:
            loop_stat = stat['loop']['loop_statements']
            for st in loop_stat:
                if 'command' in st:
                    command_list.append(Command(st['command']))
        elif 'branch' in stat:
            branch_report = branch_report + '\n'.join(stat['content']) + '\n\n'
    if branch_report:
        # add prefix
        branch_report = '\nNon-deterministic branching statement: \n' + \
                        branch_report
    return command_list, branch_report


def load_from_cache(layer, redo=False):
    '''Given a layer object, check against cache to see if that layer id exists
    if yes then load any relevant layer level information. The default
    operation is to not redo the cache. Add notices to the layer's origins
    matching the origin_str'''
    loaded = False
    if not redo:
        # check if the layer has been cached
        if layer.fs_hash in cache.get_layers():
            layer.files_analyzed = cache.cache.get(layer.fs_hash).get(
                'files_analyzed', False)
            layer.os_guess = cache.cache.get(layer.fs_hash).get(
                'os_guess', '')
            layer.pkg_format = cache.cache.get(layer.fs_hash).get(
                'pkg_format', '')
            layer.extension_info = cache.cache.get(layer.fs_hash).get(
                'extension_info', {})
            load_packages_from_cache(layer)
            load_files_from_cache(layer)
            load_notices_from_cache(layer)
            loaded = True
        else:
            # if the hash is not present in the cache, load that data from the
            # hash file
            logger.debug('Reading files in filesystem...')
            layer.add_files()
    return loaded


def load_packages_from_cache(layer):
    '''Given a layer object, populate package level information'''
    loaded = False
    raw_pkg_list = cache.get_packages(layer.fs_hash)
    if raw_pkg_list:
        logger.debug(
            'Loading packages from cache: layer \"%s\"', layer.fs_hash[:10])
        for pkg_dict in raw_pkg_list:
            pkg = Package(pkg_dict['name'])
            pkg.fill(pkg_dict)
            # collect package origins
            if 'origins' in pkg_dict.keys():
                for origin_dict in pkg_dict['origins']:
                    for notice in origin_dict['notices']:
                        pkg.origins.add_notice_to_origins(
                            origin_dict['origin_str'], Notice(
                                notice['message'], notice['level']))
            layer.add_package(pkg)
        loaded = True
    return loaded


def load_files_from_cache(layer):
    '''Given a layer object, populate file level information'''
    raw_file_list = cache.get_files(layer.fs_hash)
    if raw_file_list:
        logger.debug(
            'Loading files from cache: layer \"%s\"', layer.fs_hash[:10])
        for file_dict in raw_file_list:
            f = FileData(file_dict['name'], file_dict['path'])
            f.fill(file_dict)
            # collect file origins
            if 'origins' in file_dict.keys():
                for origin_dict in file_dict['origins']:
                    for notice in origin_dict['notices']:
                        f.origins.add_notice_to_origins(
                            origin_dict['origin_str'], Notice(
                                notice['message'], notice['level']))
            layer.add_file(f)


def load_notices_from_cache(layer):
    '''Given a layer object, populate the notices from the cache'''
    origins_list = cache.get_origins(layer.fs_hash)
    for origin_dict in origins_list:
        layer.origins.add_notice_origin(origin_dict['origin_str'])
        for notice in origin_dict['notices']:
            layer.origins.add_notice_to_origins(
                origin_dict['origin_str'], Notice(
                    notice['message'], notice['level']))


def get_total_notices(layer):
    '''Find the total number of notices in a layer'''
    count = 0
    for origin in layer.origins.origins:
        count += len(origin.notices)
    return count


def save_to_cache(image):
    '''Given an image object, save all layers to the cache'''
    for layer in image.layers:
        if layer.packages or layer.files_analyzed:
            if get_total_notices(layer) == 0:
                # if there are no new notices, we have probably pulled the
                # data from the cache. So load those notices here.
                load_notices_from_cache(layer)
            cache.add_layer(layer)


def is_empty_layer(layer):
    '''Return True if the given image layer is empty'''
    cwd = rootfs.get_untar_dir(layer.tar_file)
    if len(os.listdir(cwd)) == 0:
        return True
    return False


def get_licenses_from_deb_copyright(deb_copyright):
    '''
    Given the debian copyright text,
    1. parse each copyright text
    2. filter out all the available licenses
    3. returns a list of unique licenses found inside
    the copyright text
    '''
    collected_paragraphs = list()
    pkg_licenses = set()
    for paragraph in iter(debcon.get_paragraphs_data(deb_copyright)):
        if 'license' in paragraph:
            cp = debut_copyright.CopyrightLicenseParagraph.from_dict(paragraph)
            collected_paragraphs.append(cp)

    deb_pkg_data = debut_copyright.DebianCopyright(
        collected_paragraphs).to_dict()
    for paragraph in deb_pkg_data.get("paragraphs"):
        pkg_license = paragraph.get("license")
        if not pkg_license.startswith("*"):
            pkg_license = pkg_license.split("\n")[0]
            if pkg_license:
                pkg_licenses.add(pkg_license)

    return list(pkg_licenses)


def get_deb_package_licenses(deb_copyrights):
    '''
    Given a list of debian copyrights for the same number of packages,
    returns a list package licenses for each of the packages
    '''
    deb_licenses = list()
    for deb_copyright in deb_copyrights:
        deb_licenses.append(get_licenses_from_deb_copyright(deb_copyright))
    return deb_licenses


def remove_duplicate_layer_files(layer):
    '''Given an image layer, removes duplicate FileData objects that are found
    both at the layer and package level'''
    for layer_file in layer.files:
        for pkg in layer.packages:
            for pkg_file in pkg.files:
                if layer_file.is_equal(pkg_file):
                    layer.remove_file(layer_file.path)


def check_git_src(dockerfile_path):
    '''Given the src_path and the dockerfile path, return the git
    repository name and sha information in the format of string.
    Currently we only consider the following situation:
    - target_git_project
        - dir1
        - dir2/dockerfile
    So we only use dockerfile_path to find the git repo info.'''
    # get the path of the folder containing the dockerfile
    dockerfile_folder_path = os.path.dirname(os.path.abspath(dockerfile_path))
    # locate the top level directory
    path_to_toplevel = get_git_toplevel(dockerfile_folder_path)
    # get the path of the target folder or file
    logger.debug('looking into path: %s for git repo.', path_to_toplevel)
    comment_line = ''
    if path_to_toplevel:
        sha_info = get_git_sha(path_to_toplevel)
        # if path_to_toplevel exists, name_info should be the folder name
        name_info = os.path.basename(path_to_toplevel)
        comment_line = ('git project name: ' + name_info +
                        ', HEAD sha: ' + sha_info)
    else:
        comment_line = 'Not a git repository'
    return comment_line


def get_git_sha(path_to_toplevel):
    '''Given a absolute path to a git repository, return the HEAD sha.'''
    command = ['git', 'rev-parse', 'HEAD']
    sha_info = '(not found)'
    try:
        output = subprocess.check_output(  # nosec
            command, stderr=subprocess.DEVNULL, cwd=path_to_toplevel)
        if isinstance(output, bytes):
            sha_info = output.decode('utf-8').split('\n').pop(0)
    except subprocess.CalledProcessError:
        logger.debug("Cannot find git repo sha, toplevel path is %s",
                     path_to_toplevel)
    return sha_info


def get_git_url(dockerfile_path):
    '''Given a dockerfile_path, return url of git project which contains
    the dockerfile in a form of list.'''
    # get the path of the folder containing the dockerfile
    dockerfile_folder_path = os.path.dirname(os.path.abspath(dockerfile_path))
    command = ['git', 'remote', '-v']
    try:
        output = subprocess.check_output(  # nosec
            command, stderr=subprocess.DEVNULL, cwd=dockerfile_folder_path)
        if isinstance(output, bytes):
            lines = output.decode('utf-8').split('\n')
            # pop the last line which is an empty line
            lines.pop()
            url_list = set()
            for line in lines:
                extract_url = extract_git_url_from_line(line)
                if extract_url:
                    url_list.add(extract_url)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("Cannot find git repo url, path is %s",
                     dockerfile_folder_path)
    return url_list


def extract_git_url_from_line(line):
    '''Given a line of git remote -v output, parse the url
    line structure is '<label>\t<url> (fetch)'''
    split_line = line.split(' ')
    extract_url = ''
    # use fetch url
    if split_line[1] == '(fetch)':
        split_line = split_line[0].split('\t')
        # use https or git@ type
        full_url = split_line[1]
        if full_url.startswith('https://'):
            extract_url = full_url.lstrip('https://')
        elif full_url.startswith('http://'):
            extract_url = full_url.lstrip('http://')
        elif full_url.startswith('git'):
            extract_url = full_url.replace('git@github.com:', 'github.com/', 1)
        extract_url = extract_url.rstrip('.git')
    return extract_url


def get_git_toplevel(path):
    '''Given a path, return the absolute path to the top level directory if it
    is in a git repository. Empty string will be returned if not.
    Path should be a path to a directory not to a file.'''
    command = ['git', 'rev-parse', '--show-toplevel']
    path_to_toplevel = ''
    try:
        output = subprocess.check_output(  # nosec
            command, stderr=subprocess.DEVNULL, cwd=path)
        if isinstance(output, bytes):
            path_to_toplevel = output.decode('utf-8').split('\n').pop(0)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("Cannot find git repo toplevel, path is %s", path)
    return path_to_toplevel
