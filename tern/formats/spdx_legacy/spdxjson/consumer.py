# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
SPDXJSON document consumer
"""

import json
import logging
import os

from tern.classes.image_layer import ImageLayer
from tern.classes.package import Package
from tern.formats import consumer
from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)


class ConsumerError(Exception):
    """Exception raised if a critical error has occured"""


def get_package_from_dict(pkg_dict):
    """The SPDX JSON format contains a list of dictionaries, each containing
    the package metadata. For one package dictionary, return a Package
    object"""
    pkg_obj = Package(pkg_dict['name'])
    pkg_obj.version = ("" if pkg_dict['versionInfo'] == 'NOASSERTION'
                       else pkg_dict['versionInfo'])
    pkg_obj.proj_url = ("" if pkg_dict['downloadLocation'] == 'NONE'
                        else pkg_dict['downloadLocation'])
    pkg_obj.copyright = ("" if pkg_dict['copyrightText'] == 'NONE'
                         else pkg_dict['copyrightText'])
    return pkg_obj


def get_license_refs_dict(license_refs_list):
    """In SPDX, if the license strings extracted from package metadata is
    not a license expression it will be listed separately. Given such a
    list, return a dictionary containing license ref to extracted text"""
    license_ref_dict = {}
    if license_refs_list:
        for ref_dict in license_refs_list:
            license_ref_dict[ref_dict['licenseId']] = ref_dict['extractedText']
    return license_ref_dict


def create_image_layer(report):
    """Given a report file, create an ImageLayer object with the metadata"""
    # expect a json input, raise an error if it is not
    content = {}
    try:
        with open(os.path.abspath(report), encoding='utf-8') as f:
            content = json.load(f)
    except OSError as err:
        logger.critical("Cannot access file %s: %s", report, err)
        raise ConsumerError(f"Error with given report file: {report}") from err
    except json.JSONDecodeError as err:
        logger.critical("Cannot parse JSON in file %s: %s", report, err)
        raise ConsumerError(f"Error with given report file: {report}") from err
    # we should have some content but it may be empty
    if not content:
        raise ConsumerError("No content consumed from given report file")
    # instantiate a layer and fill it
    layer = ImageLayer("")
    # if there are license refs, make a dictionary with license refs to
    # extracted content
    refs_license = get_license_refs_dict(
        content.get('hasExtractedLicensingInfos', []))
    try:
        # we ignore the document level information and go straight
        # to the packages
        for pkg in content['packages']:
            pkg_obj = get_package_from_dict(pkg)
            pkg_obj.pkg_license = refs_license.get(pkg['licenseDeclared'])
            layer.add_package(pkg_obj)
        return layer
    except ValueError as err:
        logger.critical("Cannot find required data in report: %s", err)
        return None


class SpdxJSON(consumer.Consume):
    def consume_layer(self, reports):
        """Given a list of report files in the SPDX JSON format, created by
        the spdxjson generator, create a total list of image layer objects.
        We assume the layers are ordered in the order or report files"""
        layer_list = []
        layer_count = 1
        for report in reports:
            layer = create_image_layer(report)
            layer.layer_index = layer_count
            layer_list.append(layer)
            layer_count += 1
        return layer_list
