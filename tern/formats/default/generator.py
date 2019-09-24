# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
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
    full_license_list = []
    for image_origin in image.origins.origins:
        notes = notes + content.print_notices(image_origin, '', '\t')
    for layer in image.layers:
        if layer.import_image:
            notes = notes + print_full_report(layer.import_image)
        else:
            for layer_origin in layer.origins.origins:
                notes = notes + content.print_notices(layer_origin,
                                                      '\t', '\t\t')
            layer_pkg_list = []
            layer_license_list = []
            for package in layer.packages:
                pkg = package.name + "-" + package.version
                if pkg not in layer_pkg_list and pkg:
                    layer_pkg_list.append(pkg)
                if package.pkg_license not in layer_license_list and \
                        package.pkg_license:
                    layer_license_list.append(package.pkg_license)
                    if package.pkg_license not in full_license_list:
                        full_license_list.append(package.pkg_license)
            # Collect packages + licenses in the layer
            notes = notes + formats.layer_packages_list.format(
                list=", ".join(layer_pkg_list) if layer_pkg_list else 'None')
            notes = notes + formats.layer_licenses_list.format(list=", ".join(
                layer_license_list) if layer_license_list else 'None')
            notes = notes + formats.package_demarkation
    # Collect the full list of licenses from all the layers
    licenses = formats.full_licenses_list.format(list=", ".join(
        full_license_list) if full_license_list else 'None')
    return notes + licenses


class Default(generator.Generate):
    def generate(self, image_obj_list):
        '''Generate a default report'''
        report = formats.disclaimer.format(
            version_info=content.get_tool_version())
        logger.debug('Creating a detailed report of components in image...')
        for image in image_obj_list:
            report = report + print_full_report(image)
        return report
