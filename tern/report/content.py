# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to generate content for the report
"""

from tern.analyze.default.command_lib import command_lib
from tern.report import formats
from tern.utils.general import get_git_rev_or_version


def get_layer_packages_licenses(layer):
    '''Given a image layer collect complete list of package licenses'''
    pkg_licenses = set()
    for package in layer.packages:
        package_licenses = get_package_licenses(package)
        for package_license in package_licenses:
            pkg_licenses.add(package_license)
    return list(pkg_licenses)


def get_layer_files_licenses(layer):
    '''Given a image layer collect complete list of file licenses'''
    file_level_licenses = set()
    for f in layer.files:
        for license_expression in f.license_expressions:
            if license_expression:
                file_level_licenses.add(license_expression)
    return list(file_level_licenses)


def get_licenses_only(image_obj_list):
    '''Returns a list of all the lists found in images'''
    full_licenses = set()
    for image in image_obj_list:
        for layer in image.layers:
            pkg_licenses = get_layer_packages_licenses(layer)
            for pkg_license in pkg_licenses:
                full_licenses.add(pkg_license)

            file_level_licenses = get_layer_files_licenses(layer)
            for file_level_license in file_level_licenses:
                full_licenses.add(file_level_license)
    return list(full_licenses)


def get_package_licenses(package):
    '''Given a package collect complete list of package licenses'''
    pkg_licenses = set()
    if package.pkg_license:
        pkg_licenses.add(package.pkg_license)

    if package.pkg_licenses:
        for pkg_license in package.pkg_licenses:
            if pkg_license:
                pkg_licenses.add(pkg_license)
    return list(pkg_licenses)


def get_tool_version():
    '''Return a string describing the version and where it came from'''
    ver_type, ver = get_git_rev_or_version()
    if ver_type == 'commit':
        return formats.commit_version.format(commit_sha=ver)
    return formats.packaged_version.format(version=ver)


def print_invoke_list(info_dict, info):
    '''Print out the list of command snippets that get invoked to retrive
    package information.
    info_dict: get_base_listing or get_command_listing from
    command_lib/command_lib.py
    see command_lib/command_lib.py for a list of supported info items'''
    report = ''
    if 'invoke' in info_dict[info]:
        report = report + info + ':\n'
        for step in range(1, len(info_dict[info]['invoke'].keys()) + 1):
            if 'container' in info_dict[info]['invoke'][step]:
                report = report + formats.invoke_in_container
                for snippet in info_dict[info]['invoke'][step]['container']:
                    report = report + '\t' + snippet + '\n'
    else:
        for value in info_dict[info]:
            report = report + ' ' + value
    report = report + '\n'
    return report


def print_base_invoke(key):
    '''Given the key in the base library, return a string containing
    the command_lib/base.yml'''
    info = command_lib.get_base_listing(key)
    report = ''
    for item in command_lib.base_keys:
        if item in info.keys():
            report = report + print_invoke_list(info, item)
    report = report + '\n'
    return report


def print_package_invoke(command_name):
    '''Given the command name to look up in the snippet library and the
    package name, return a string with the list of commands that will be
    invoked in the container'''
    report = ''
    command_listing = command_lib.get_command_listing(command_name)
    if command_listing:
        pkg_list = command_listing['packages']
        for pkg_dict in pkg_list:
            report = report + print_invoke_list(pkg_dict, 'version')
            report = report + print_invoke_list(pkg_dict, 'license')
            report = report + print_invoke_list(pkg_dict, 'proj_url')
            report = report + print_invoke_list(pkg_dict, 'deps')
    return report


def print_notices(notice_origin, origin_pfx, notice_pfx):
    '''Given a NoticeOrigin object with a prefix (like a series of tabs)
    for the origin and the notice messages, return the notes'''
    notes = origin_pfx + notice_origin.origin_str + ':\n'
    for notice in notice_origin.notices:
        notes = notes + notice_pfx + notice.level + ': ' + \
            notice.message + '\n'
    return notes
