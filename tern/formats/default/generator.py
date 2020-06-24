# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
default report generator
"""

import logging

from tern.report import formats
from tern.formats import generator
from tern.report import content
from tern.utils import constants


# global logger
logger = logging.getLogger(constants.logger_name)


def print_full_report(image):
    '''Given an image, go through the Origins object and collect all the
    notices for the image, layers and packages'''
    notes = ''
    for image_origin in image.origins.origins:
        notes = notes + content.print_notices(image_origin, '', '\t')

    # collect extension's header per layer
    headers = get_extension_headers(image.layers)
    for header in headers:
        notes = notes + header + '\n\n'

    for layer in image.layers:
        if layer.import_image:
            notes = notes + print_full_report(layer.import_image)
        else:
            notes = notes + get_layer_notices(layer)
            (layer_pkg_list, layer_license_list,
             file_level_licenses) = get_layer_info_list(layer)
            # Collect files + packages + licenses in the layer
            notes += formats.layer_file_licenses_list.format(
                list=file_level_licenses)
            notes += formats.layer_packages_list.format(
                list=", ".join(layer_pkg_list) if layer_pkg_list else 'None')
            notes += formats.layer_licenses_list.format(list=", ".join(
                layer_license_list) if layer_license_list else 'None')
            notes = notes + formats.package_demarkation
    return notes


def get_layer_notices(layer):
    '''
    Given a image layer, collect all notices attached
    to it.
    '''
    notices = ''
    if len(layer.origins.origins) == 0:
        notices = '\tLayer {0}:\n'.format(layer.layer_index)
    else:
        for layer_origin in layer.origins.origins:
            notices += content.print_notices(layer_origin, '\t', '\t\t')

    return notices


def get_extension_headers(layers):
    '''
    Given all image layers, collect header string set
    by extension on each layer level.
    '''
    headers = set()
    for layer in layers:
        layer_headers = layer.extension_info.get("headers", set())
        for layer_header in layer_headers:
            headers.add(layer_header)

    return headers


def get_layer_info_list(layer):
    '''Given a layer, collect files + packages + licenses in the layer,
    return them as lists.'''
    layer_pkg_list = []
    layer_license_list = []
    layer_file_licenses_list = []
    file_level_licenses = None

    for f in layer.files:
        layer_file_licenses_list.extend(f.license_expressions)

    layer_file_licenses_list = list(set(layer_file_licenses_list))
    if layer_file_licenses_list:
        file_level_licenses = ", ".join(layer_file_licenses_list)

    for package in layer.packages:
        pkg = package.name + "-" + package.version
        if pkg not in layer_pkg_list and pkg:
            layer_pkg_list.append(pkg)

        package_licenses = content.get_package_licenses(package)
        for package_license in package_licenses:
            if package_license not in layer_license_list:
                layer_license_list.append(package_license)

    return layer_pkg_list, layer_license_list, file_level_licenses


def print_licenses_only(image_obj_list):
    '''Print a complete list of licenses for all images'''
    full_license_list = content.get_licenses_only(image_obj_list)
    # Collect the full list of licenses from all the layers
    licenses = formats.full_licenses_list.format(list=", ".join(
        full_license_list) if full_license_list else 'None')
    return licenses


class Default(generator.Generate):
    def generate(self, image_obj_list):
        '''Generate a default report'''
        report = formats.disclaimer.format(
            version_info=content.get_tool_version())
        logger.debug('Creating a detailed report of components in image...')
        for image in image_obj_list:
            report = report + print_full_report(image)
        return report + print_licenses_only(image_obj_list)
