# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
JSON document generator
"""

import json
import logging
import os

from tern.classes.image_layer import ImageLayer
from tern.classes.package import Package
from tern.classes.file_data import FileData
from tern.formats import consumer
from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)


class ConsumerError(Exception):
    """Exception raised if a critical error has occured"""


def create_image_layer(report):
    """Given a report file, create an ImageLayer object with the metadata"""
    # expect a json input, raise an error if it is not
    content = {}
    try:
        f = open(os.path.abspath(report))
        content = json.load(f)
    except OSError as err:
        logger.critical("Cannot access file %s: %s", report, err)
        raise ConsumerError(f"Error with given report file: {report}")
    except json.JSONDecodeError as err:
        logger.critical("Cannot parse JSON in file %s: %s", report, err)
        raise ConsumerError(f"Error with given report file: {report}")
    # we should have some content but it may be empty
    if not content:
        raise ConsumerError("No content consumed from given report file")
    # instantiate a layer and fill it
    layer = ImageLayer("")
    try:
        layer.os_guess = content['os_guess']
        for pkg in content['packages']:
            pkg_obj = Package(pkg['name'])
            pkg_obj.fill(pkg)
            layer.add_package(pkg_obj)
        for filedict in content['files']:
            file_obj = FileData(filedict['name'], filedict['path'])
            file_obj.fill(filedict)
            layer.add_file(file_obj)
        return layer
    except ValueError as err:
        logger.critical("Cannot find required data in report: %s", err)
        return None


class JSON(consumer.Consume):
    def consume_layer(self, reports):
        """Given a list json report files, created by the json generator,
        create a corresponding list of image layer objects. We assume the
        layers are ordered in the order or report files"""
        layer_list = []
        layer_count = 1
        for report in reports:
            layer = create_image_layer(report)
            layer.layer_index = layer_count
            layer_list.append(layer)
            layer_count += 1
        return layer_list
