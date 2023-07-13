# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
SPDX YAML document generator
"""
from typing import List

from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.formats import generator
from tern.formats.spdx_new.spdx_formats_helper import get_spdx_from_image_list, get_spdx_from_layer


class SpdxYAML(generator.Generate):
    def generate(self, image_obj_list: List[Image], format_version: str, print_inclusive=False) -> str:
        return get_spdx_from_image_list(image_obj_list, "YAML", format_version)

    def generate_layer(self, layer: ImageLayer, format_version: str) -> str:
        return get_spdx_from_layer(layer, "YAML", format_version)
