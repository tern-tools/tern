# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Handle imports and logging for different SPDX formats
"""
import io
import logging
from typing import Callable, IO, List

from spdx_tools.spdx.model import Document

from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.formats.spdx.spdx import SPDX
from tern.formats.spdx_new.make_spdx_model import make_spdx_model, make_spdx_model_snapshot
from tern.utils import constants

logger = logging.getLogger(constants.logger_name)


def get_spdx_from_image_list(image_obj_list: List[Image], spdx_format: str, spdx_version: str) -> str:
    """Generate an SPDX document
    WARNING: This assumes that the list consists of one image or the base
    image and a stub image, in which case, the information in the stub
    image is not applicable in the SPDX case as it is an empty image
    object with no metadata as nothing got built.

    For the sake of SPDX, an image is a 'Package' which 'CONTAINS' each
    layer which is also a 'Package' which 'CONTAINS' the real Packages"""
    logger.debug(f"Generating SPDX {spdx_format} document...")

    spdx_document: Document = make_spdx_model(image_obj_list, spdx_version)

    return convert_document_to_serialized_string(spdx_document, spdx_format)


def get_spdx_from_layer(layer: ImageLayer, spdx_format: str, spdx_version: str) -> str:
    """Generate an SPDX document containing package and file information
    at container build time"""
    logger.debug(f"Generating SPDX {spdx_format} snapshot document...")

    template = SPDX()
    spdx_document: Document = make_spdx_model_snapshot(layer, template, spdx_version)

    return convert_document_to_serialized_string(spdx_document, spdx_format)


def convert_document_to_serialized_string(spdx_document: Document, spdx_format: str) -> str:
    if spdx_format == "JSON":
        from spdx_tools.spdx.writer.json.json_writer import write_document_to_stream
        return get_serialized_document_string(spdx_document, write_document_to_stream)
    if spdx_format == "YAML":
        from spdx_tools.spdx.writer.yaml.yaml_writer import write_document_to_stream
        return get_serialized_document_string(spdx_document, write_document_to_stream)
    if spdx_format == "XML":
        from spdx_tools.spdx.writer.xml.xml_writer import write_document_to_stream
        return get_serialized_document_string(spdx_document, write_document_to_stream)
    if spdx_format == "RDF-XML":
        return get_serialized_rdf_document_string(spdx_document)
    if spdx_format == "Tag-Value":
        from spdx_tools.spdx.writer.tagvalue.tagvalue_writer import write_document_to_stream
        return get_serialized_document_string(spdx_document, write_document_to_stream)


def get_serialized_document_string(spdx_document: Document, writer_function: Callable[[Document, IO[str]], str]) -> str:
    with io.StringIO() as stream:
        writer_function(spdx_document, stream, validate=False)
        return stream.getvalue()


def get_serialized_rdf_document_string(spdx_document: Document) -> str:
    from spdx_tools.spdx.writer.rdf.rdf_writer import write_document_to_stream
    with io.BytesIO() as stream:
        write_document_to_stream(spdx_document, stream, validate=False)
        return stream.getvalue().decode("UTF-8")
