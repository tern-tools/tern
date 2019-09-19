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
    pkg_list = []
    license_list = []
    for image_origin in image.origins.origins:
        notes = notes + content.print_notices(image_origin, '', '\t')
    for layer in image.layers:
        if layer.import_image:
            notes = notes + print_full_report(layer.import_image)
        else:
            for layer_origin in layer.origins.origins:
                notes = notes + content.print_notices(layer_origin,
                                                      '\t', '\t\t')
            for package in layer.packages:
                pkg = package.name + "-" + package.version
                if pkg not in pkg_list and pkg:
                    pkg_list.append(pkg)
                if package.pkg_license not in license_list and \
                        package.pkg_license:
                    license_list.append(package.pkg_license)
            notes = notes + formats.package_demarkation
    packages = formats.packages_list.format(list=", ".join(pkg_list) if
                                            pkg_list else 'None')
    licenses = formats.licenses_list.format(list=", ".join(license_list) if
                                            license_list else 'None')
    return notes + packages + formats.package_demarkation + licenses


class Default(generator.Generate):
    def generate(self, image_obj_list):
        '''Generate a default report'''
        report = formats.disclaimer.format(
            version_info=content.get_tool_version())
        logger.debug('Creating a detailed report of components in image...')
        for image in image_obj_list:
            report = report + print_full_report(image)
        return report
