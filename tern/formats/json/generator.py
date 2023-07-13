# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
JSON document generator
"""

import json
import logging

from tern.formats import generator
from tern.utils import constants

logger = logging.getLogger(constants.logger_name)

class JSON(generator.Generate):
    def generate(self, image_obj_list, format_version: str, print_inclusive=False):
        '''Given a list of image objects, create a json object string'''
        image_list = []
        if format_version is not None:
            logger.warning("The version parameter is not supported for JSON.")

        for image in image_obj_list:
            image_list.append({'image': image.to_dict()})
        image_dict = {'images': image_list}
        return json.dumps(image_dict)

    def generate_layer(self, layer, format_version: str):
        """Create a json object for one layer"""
        if format_version is not None:
            logger.warning("The version parameter is not supported for JSON.")

        return json.dumps(layer.to_dict())
