'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

from command_lib.command_lib import get_base_listing
from command_lib.command_lib import get_command_listing
from command_lib.command_lib import FormatAwk
from command_lib.command_lib import check_for_unique_package
import formats

'''
Functions to generate content for the report
'''

def print_invoke_list(info_dict, info):
    '''Print out the list of command snippets that get invoked to retrive
    package information.
    info_dict: get_base_listing or get_command_listing from
    command_lib/command_lib.py
    info: the required key (niames, versions, licenses, etc)'''
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


def print_base_image_info(base_image_tag):
    '''Given the base image and tag in a tuple return a string containing
    the command_lib/base.yml'''
    info = get_base_listing(base_image_tag)
    report = ''
    report = report + print_invoke_list(info, 'names')
    report = report + print_invoke_list(info, 'versions')
    report = report + print_invoke_list(info, 'licenses')
    report = report + print_invoke_list(info, 'src_urls')
    report = report + '\n'
    return report


def print_package_info(command_name, package_name):
    '''Given the command name to look up in the snippet library and the
    package name, return a string with the list of commands that will be
    invoked in the container'''
    report = ''
    command_listing = get_command_listing(command_name)
    if command_listing:
        pkg_list = command_listing['packages']
        pkg_dict = check_for_unique_package(pkg_list, package_name)
        report = report + print_invoke_list(pkg_dict, 'version').format_map(
            FormatAwk(package=package_name))
        report = report + print_invoke_list(pkg_dict, 'license').format_map(
            FormatAwk(package=package_name))
        report = report + print_invoke_list(pkg_dict, 'src_url').format_map(
            FormatAwk(package=package_name))
        report = report + print_invoke_list(pkg_dict, 'deps').format_map(
            FormatAwk(package=package_name))
    return report
