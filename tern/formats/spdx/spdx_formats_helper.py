# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 VMWare, Inc. All Rights Reserved.
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
from tern.formats.spdx.spdx_template import SPDX
from tern.formats.spdx.make_spdx_model import make_spdx_model, make_spdx_model_snapshot
from tern.utils import constants

logger = logging.getLogger(constants.logger_name)

SPDX_VERSION_MAPPING = {
    "2.2": "SPDX-2.2",
    "2.3": "SPDX-2.3",
}


def get_spdx_from_image_list(image_obj_list: List[Image], spdx_format: str, spdx_version: str) -> str:
    """Given a list of image objects and an SPDX format and version,
    return the serialized string of the SPDX document representation in that format and version
    generated from the image objects.

    WARNING: This assumes that the list consists of one image or the base
    image and a stub image, in which case, the information in the stub
    image is not applicable in the SPDX case as it is an empty image
    object with no metadata as nothing got built.

    For the sake of SPDX, an image is a 'Package' which 'CONTAINS' each
    layer which is also a 'Package' which 'CONTAINS' the real Packages"""
    logger.debug(f"Generating SPDX %s document..." % spdx_format)

    if spdx_version not in SPDX_VERSION_MAPPING:
        raise ValueError(f"SPDX version {spdx_version} is not supported by tern.")

    spdx_document: Document = make_spdx_model(image_obj_list, SPDX_VERSION_MAPPING[spdx_version])

    return convert_document_to_serialized_string(spdx_document, spdx_format)


def get_spdx_from_layer(layer: ImageLayer, spdx_format: str, spdx_version: str) -> str:
    """Given an Image layer and an SPDX format and version,
    returns the serialized string of the SPDX document containing package and file information
    at container build time"""
    logger.debug("Generating SPDX %s snapshot document..." % spdx_format)

    if spdx_version not in SPDX_VERSION_MAPPING:
        raise ValueError(f"SPDX version {spdx_version} is not supported by tern.")

    template = SPDX()
    spdx_document: Document = make_spdx_model_snapshot(layer, template, SPDX_VERSION_MAPPING[spdx_version])

    return convert_document_to_serialized_string(spdx_document, spdx_format)


def convert_document_to_serialized_string(spdx_document: Document, spdx_format: str) -> str:
    """Given an SPDX document and a format, return the serialized string of the
    representation of that document in the specified format."""
    # pylint: disable=wrong-import-position
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
    # pylint: enable=wrong-import-position


def get_serialized_document_string(spdx_document: Document, writer_function: Callable[[Document, IO[str]], str]) -> str:
    with io.StringIO() as stream:
        writer_function(spdx_document, stream, validate=False)
        return stream.getvalue()


def get_serialized_rdf_document_string(spdx_document: Document) -> str:
    # pylint: disable=wrong-import-position
    from spdx_tools.spdx.writer.rdf.rdf_writer import write_document_to_stream
    # pylint: enable=wrong-import-position
    with io.BytesIO() as stream:
        write_document_to_stream(spdx_document, stream, validate=False)
        return stream.getvalue().decode("UTF-8")
