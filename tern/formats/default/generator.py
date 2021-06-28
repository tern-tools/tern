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
from prettytable import PrettyTable


# global logger
logger = logging.getLogger(constants.logger_name)


def print_full_report(image, print_inclusive):
    '''Generate a report for:
        1. Full image if image.load_until_layer is 0
        2. Only layer image.load_until_layer if print_inclusive is False
        3. Layers up to image.load_until_layer if print_inclusive is True
    Goes through the Origins object and collects all necessary (as outlined
    above) notices for the image, layers and packages'''

    notes = ''
    for image_origin in image.origins.origins:
        notes = notes + content.print_notices(image_origin, '', '\t')

    # collect extension's header per layer
    headers = get_extension_headers(image.layers)
    for header in headers:
        notes = notes + header + '\n\n'

    for layer in image.layers:
        if image.load_until_layer != 0 and \
           layer.layer_index is not image.load_until_layer and \
           print_inclusive is False:
            continue
        if layer.import_image:
            notes = notes + print_full_report(
                layer.import_image, print_inclusive)
        else:
            notes += print_layer_report(layer)
            notes += formats.package_demarkation
    return notes


def print_layer_report(layer):
    """Generate a report for a given layer"""
    notes = get_layer_notices(layer)
    filelicenses, pkgs_table = get_layer_info_list(layer)
    notes += formats.layer_file_licenses_list.format(
        list=filelicenses)
    if pkgs_table:
        notes += formats.layer_packages_header.format('\n')
        for line in pkgs_table.splitlines():
            notes += '\t' + line + '\n'
    else:
        notes += formats.layer_packages_header.format("None\n")
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
    return them as a PrettyTable string object.'''
    layer_file_licenses_list = []
    file_level_licenses = None
    package_list = PrettyTable()
    package_list.field_names = ["Package", "Version", "License", "Pkg Format"]
    package_list.align = "l"
    package_list.print_empty = False

    for f in layer.files:
        layer_file_licenses_list.extend(f.licenses)

    layer_file_licenses_list = list(set(layer_file_licenses_list))
    if layer_file_licenses_list:
        file_level_licenses = ", ".join(layer_file_licenses_list)

    for package in layer.packages:
        package_list.add_row([package.name, package.version,
                              package.pkg_license, package.pkg_format])

    return file_level_licenses, package_list.get_string()


def print_licenses_only(image_obj_list):
    '''Print a complete list of licenses for all images'''
    full_license_list = content.get_licenses_only(image_obj_list)
    # Collect the full list of licenses from all the layers
    licenses = formats.full_licenses_list.format(list=", ".join(
        full_license_list) if full_license_list else 'None')
    return licenses


class Default(generator.Generate):
    def generate(self, image_obj_list, print_inclusive=False):
        '''Generate a default report'''
        report = formats.disclaimer.format(
            version_info=content.get_tool_version())
        logger.debug('Creating a detailed report of components in image...')
        report_only = False
        for image in image_obj_list:
            if not print_inclusive and image.load_until_layer != 0:
                report_only = True
            report = report + print_full_report(image, print_inclusive)
        if report_only:
            return report
        return report + print_licenses_only(image_obj_list)

    def generate_layer(self, layer):
        """Generate a default report for one layer object"""
        report = formats.disclaimer.format(
            version_info=content.get_tool_version())
        logger.debug("Generating summary report for layer...")
        return report + print_layer_report(layer)
