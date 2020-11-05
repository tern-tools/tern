# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to bundle results into an image object
"""

import logging
import os

from tern.utils import constants
from tern.classes.package import Package
from tern.classes.file_data import FileData

# global logger
logger = logging.getLogger(constants.logger_name)


def get_pkg_dict_for_index(attr_list, index):
    """Given the package dictionary with attribute lists of the form
    {'name': [...], 'version': [...],...} and an index, return
    a package dictionary of the form {'name': x1, 'version': x2,...} for that
    index"""
    pkg_dict = {}
    for key in attr_list.keys():
        if key == 'files':
            # convert file paths into FileData dictionaries
            fd_list = []
            for filepath in attr_list['files'][index]:
                fd_dict = FileData(os.path.split(
                    filepath)[1], filepath).to_dict()
                fd_list.append(fd_dict)
            pkg_dict.update({'files': fd_list})
        else:
            pkg_dict.update({key: attr_list[key][index]})
    return pkg_dict


def convert_to_pkg_dicts(attr_lists):
    '''attr_lists is what gets returned after collecting individual
    metadata as a list. It looks like this if property collected:
        {'names': [....], 'versions': [...], 'licenses': [...], ....}
    Convert these into a package dictionary expected by the Package
    Object'''
    mapping = {'name': 'names',
               'version': 'versions',
               'pkg_license': 'licenses',
               'copyright': 'copyrights',
               'proj_url': 'proj_urls',
               'pkg_licenses': 'pkg_licenses',
               'files': 'files'}
    pkg_list = []
    len_names = len(attr_lists['names'])
    # make a list of keys that correspond with package property names
    filtered_attr_list = {}
    for key, value in mapping.items():
        if value in attr_lists.keys():
            if len(attr_lists[value]) == len_names:
                filtered_attr_list.update({key: attr_lists[value]})
            else:
                logger.warning("Inconsistent lengths for key: %s", value)
    # convert each of the keys into package dictionaries
    for index in range(0, len_names):
        pkg_list.append(get_pkg_dict_for_index(filtered_attr_list, index))
    return pkg_list


def fill_pkg_results(image_layer, pkg_list_dict):
    """Fill results from collecting package information into the image layer
    object"""
    if 'names' in pkg_list_dict and len(pkg_list_dict['names']) > 1:
        pkg_list = convert_to_pkg_dicts(pkg_list_dict)
        for pkg_dict in pkg_list:
            pkg = Package(pkg_dict['name'])
            pkg.fill(pkg_dict)
            image_layer.add_package(pkg)
