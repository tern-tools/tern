# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
SPDX JSON document generator
"""
import logging
from typing import List

from spdx_tools.spdx.model import Document
from spdx_tools.spdx.writer.json.json_writer import write_document_to_stream

from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.formats import generator
from tern.formats.spdx.spdx import SPDX
from tern.formats.spdx_new.general_helpers import get_serialized_document_string
from tern.formats.spdx_new.make_spdx_model import make_spdx_model, make_spdx_model_snapshot
from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)


class SpdxJSON(generator.Generate):
    def generate(self, image_obj_list: List[Image], print_inclusive=False) -> str:
        """Generate an SPDX document
        WARNING: This assumes that the list consists of one image or the base
        image and a stub image, in which case, the information in the stub
        image is not applicable in the SPDX case as it is an empty image
        object with no metadata as nothing got built.

        For the sake of SPDX, an image is a 'Package' which 'CONTAINS' each
        layer which is also a 'Package' which 'CONTAINS' the real Packages"""
        logger.debug("Generating SPDX JSON document...")

        spdx_document: Document = make_spdx_model(image_obj_list)

        return get_serialized_document_string(spdx_document, write_document_to_stream)

    def generate_layer(self, layer: ImageLayer) -> str:
        """Generate an SPDX document containing package and file information
        at container build time"""
        logger.debug("Generating SPDX JSON snapshot document...")
        template = SPDX()
        spdx_document: Document = make_spdx_model_snapshot(layer, template)

        return get_serialized_document_string(spdx_document, write_document_to_stream)
