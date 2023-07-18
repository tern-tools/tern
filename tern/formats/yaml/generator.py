# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
YAML document generator
"""
import logging

import yaml
from tern.report import formats
from tern.utils import constants
from tern.utils.general import get_git_rev_or_version
from tern.formats import generator

logger = logging.getLogger(constants.logger_name)

def print_yaml_report(image):
    '''Given an image object, create a yaml report'''
    image_dict = {}
    image_dict.update({'image': image.to_dict()})
    return yaml.dump(image_dict, default_flow_style=False)


class YAML(generator.Generate):
    def generate(self, image_obj_list, spdx_version: str, print_inclusive=False):
        '''Generate a yaml report'''
        if spdx_version is not None:
            logger.warning("The SPDX version parameter is not supported for YAML.")

        report = formats.disclaimer_yaml.format(
            version_info=get_git_rev_or_version())
        for image in image_obj_list:
            report = report + print_yaml_report(image)
        return report

    def generate_layer(self, layer, spdx_version: str):
        """Generate a yaml report for the given layer object"""
        if spdx_version is not None:
            logger.warning("The SPDX version parameter is not supported for YAML.")

        return yaml.dump(layer.to_dict(), default_flow_style=False)
