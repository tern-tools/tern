# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
JSON document generator
"""

import json
from tern.formats import generator


class JSON(generator.Generate):
    def generate(self, image_obj_list, print_inclusive=False):
        '''Given a list of image objects, create a json object string'''
        image_list = []
        for image in image_obj_list:
            image_list.append({'image': image.to_dict()})
        image_dict = {'images': image_list}
        return json.dumps(image_dict)

    def generate_layer(self, layer):
        """Create a json object for one layer"""
        return json.dumps(layer.to_dict())
