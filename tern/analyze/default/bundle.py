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


def convert_to_pkg_dicts(pkg_dict):
    '''The pkg_dict is what gets returned after collecting individual
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
    len_names = len(pkg_dict['names'])
    # make a list of keys that correspond with package property names
    new_dict = {}
    for key, value in mapping.items():
        if value in pkg_dict.keys():
            if len(pkg_dict[value]) == len_names:
                new_dict.update({key: pkg_dict[value]})
            else:
                logger.warning("Inconsistent lengths for key: %s", value)
    # convert each of the keys into package dictionaries
    for index, _ in enumerate(new_dict['name']):
        a_pkg = {}
        for key, value in new_dict.items():
            if key == 'files':
                # update the list with FileData objects in dictionary format
                fd_list = []
                for filepath in value[index]:
                    fd_dict = FileData(
                        os.path.split(filepath)[1], filepath).to_dict()
                    fd_list.append(fd_dict)
                a_pkg.update({'files': fd_list})
            else:
                a_pkg.update({key: value[index]})
        pkg_list.append(a_pkg)
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
