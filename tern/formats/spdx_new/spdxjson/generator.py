# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 VMWare, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
SPDX JSON document generator
"""
from typing import List

from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.formats import generator
from tern.formats.spdx_new.spdx_formats_helper import get_spdx_from_image_list, get_spdx_from_layer


class SpdxJSON(generator.Generate):
    def generate(self, image_obj_list: List[Image], spdx_version: str, print_inclusive=False) -> str:
        if spdx_version is None:
            spdx_version = "2.2"
        return get_spdx_from_image_list(image_obj_list, "JSON", spdx_version)

    def generate_layer(self, layer: ImageLayer, spdx_version) -> str:
        return get_spdx_from_layer(layer, "JSON", spdx_version)
