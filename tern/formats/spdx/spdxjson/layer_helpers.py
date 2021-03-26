# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helpers for layer information
Layers for SPDX act like a Package
"""
import logging
import os

from tern.utils import constants
from tern.formats.spdx import spdx_common
from tern.formats.spdx.spdxjson import formats as json_formats
from tern.report import content


# global logger
logger = logging.getLogger(constants.logger_name)


def get_layer_extracted_licenses(layer_obj):
    '''Given an image_obj, return a unique list of extractedText dictionaries
    that contain all the file and package license key-value pairs for a
    LicenseRef and its corresponding plain text. The dictionaries will
    contain the following information:
        {
            "extractedText": "Plain text of license",
            "licenseId": "Corresponding LicenseRef"
        }'''

    unique_licenses = set()
    # Get all of the unique file licenses, if they exist
    unique_licenses.update(spdx_common.get_layer_licenses(layer_obj))
    # Next, collect any package licenses not already accounted for
    for package in layer_obj.packages:
        if package.pkg_license:
            unique_licenses.add(package.pkg_license)
    extracted_texts = []
    for lic in list(unique_licenses):
        extracted_texts.append(json_formats.get_extracted_text_dict(
            extracted_text=lic, license_ref=spdx_common.get_license_ref(
                lic)))
    return extracted_texts


def get_image_layer_relationships(image_obj):
    '''Given an image object, return a list of dictionaries describing the
    relationship between each layer "package" and the image and packages
    related to it.
    For SPDX JSON format this will typically look like:
    {
      "spdxElementId" : "SPDXRef-image",
      "relatedSpdxElement" : "SPDXRef-layer",
      "relationshipType" : "CONTAINS"
    }'''
    layer_relationships = []
    image_ref = spdx_common.get_image_spdxref(image_obj)

    # Required - DOCUMENT_DESCRIBES relationship
    layer_relationships.append(json_formats.get_relationship_dict(
        json_formats.spdx_id, image_ref, 'DESCRIBES'))

    for index, layer in enumerate(image_obj.layers):
        layer_ref = spdx_common.get_layer_spdxref(layer)
        # Create a list of dictionaries.
        # First, add dictionaries for the layer relationship to the image
        layer_relationships.append(json_formats.get_relationship_dict(
            image_ref, layer_ref, 'CONTAINS'))
        # Next, add dictionary of the layer relationship to other layers
        if index != 0:
            prev_layer_ref = spdx_common.get_layer_spdxref(
                image_obj.layers[index - 1])
            layer_relationships.append(json_formats.get_relationship_dict(
                prev_layer_ref, layer_ref, 'HAS_PREREQUISITE'))
        # Finally, add package releationships for the layer
        if layer.packages:
            for package in layer.packages:
                pkg_ref = spdx_common.get_package_spdxref(package)
                layer_relationships.append(json_formats.get_relationship_dict(
                    layer_ref, pkg_ref, 'CONTAINS'))

    return layer_relationships


def get_layer_snapshot_relationships(layer_obj, docref):
    """Given a layer object, and the SPDX ref of the document, return a list
    of dictionaries describing the relationship between the snapshot document
    and the packages listed therein"""
    relationships = []

    # document level DESCRIBES
    relationships.append(json_formats.get_relationship_dict(
        json_formats.spdx_id, docref, 'DESCRIBES'))
    # package relationships
    for package in layer_obj.packages:
        pkg_ref = spdx_common.get_package_spdxref(package)
        relationships.append(json_formats.get_relationship_dict(
            docref, pkg_ref, 'CONTAINS'))
    return relationships


def get_layer_package_comment(layer_obj):
    '''Return a package comment string value for a list of NoticeOrigin
    objects for the given layer object'''
    comment = ''
    if "headers" in layer_obj.extension_info.keys():
        for header in layer_obj.extension_info.get("headers"):
            comment += header
            comment += '\n'
    if not layer_obj.origins.is_empty():
        for notice_origin in layer_obj.origins.origins:
            comment += content.print_notices(notice_origin, '', '\t')
    return comment


def get_layer_file_data_list(layer_obj):
    '''Given a layer object return the SPDX list of file refs in the layer.
    Return an empty string if the files are not analyzed'''
    layer_lics = []
    if layer_obj.files_analyzed:
        layer_checksum = spdx_common.get_layer_checksum(layer_obj)
        # some files are located in different places in the filesystem
        # they would occur as duplicates in this list
        # keep a list of previously printed file spdx-refs
        file_refs = set()
        # file data
        for filedata in layer_obj.files:
            # we use the layer checksum as the layer id
            file_ref = spdx_common.get_file_spdxref(filedata, layer_checksum)
            if file_ref not in file_refs:
                layer_lics.append(spdx_common.get_file_spdxref(
                    filedata, layer_checksum))
                file_refs.add(file_ref)
    return layer_lics


def get_layer_dict(layer_obj):
    '''Given an layer object, return a SPDX JSON/dictionary representation
    of the layer. An image layer in SPDX behaves like a Package. The analyzed
    files will go in a separate dictionary for the JSON document.'''

    layer_dict = {
        'name': os.path.basename(layer_obj.tar_file),
        'SPDXID': spdx_common.get_layer_spdxref(layer_obj),
        'fileName': layer_obj.tar_file,
        'downloadLocation': 'NONE',
        'filesAnalyzed': 'true' if layer_obj.files_analyzed else 'false',
        'checksums': [{
            'algorithm':
                spdx_common.get_layer_checksum(layer_obj).split(': ')[0],
            'checksumValue':
                spdx_common.get_layer_checksum(layer_obj).split(': ')[1]
        }],
        'licenseConcluded': 'NOASSERTION',  # always NOASSERTION
        'licenseDeclared': 'NOASSERTION',  # always NOASSERTION
        'copyrightText': 'NOASSERTION',  # always NOASSERTION
    }

    # Only include layer file information if file data is available
    if layer_obj.files_analyzed:
        layer_dict['hasFiles'] = get_layer_file_data_list(layer_obj)

    # packageVerificationCode must be omitted if filesAnalyzed is false
    if layer_obj.files_analyzed:
        layer_dict['packageVerificationCode'] = {
            'packageVerificationCodeValue':
            spdx_common.get_layer_verification_code(layer_obj)
        }

    # Include layer package comment only if it exists
    layer_pkg_comment = get_layer_package_comment(layer_obj)
    if layer_pkg_comment:
        layer_dict['comment'] = layer_pkg_comment

    # Include layer licenses from files only if they exist
    # List will be blank if no filedata information exists
    layer_licenses = spdx_common.get_layer_licenses(layer_obj)
    layer_license_refs = []
    if layer_licenses:
        # Use the layer LicenseRef in the list instead of license expression
        for lic in layer_licenses:
            layer_license_refs.append(spdx_common.get_license_ref(lic))
        layer_dict['licenseInfoFromFiles'] = layer_license_refs

    return layer_dict


def get_layers_list(image_obj):
    '''Given an image object for SPDX, return a list of SPDX dictionary
    representations of each of the layers in the image. Each layer will be
    represented as a package and hence follows the JSON spec for packages.
        name
        versionInfo
        downloadLocation'''
    layer_dicts = []
    for layer in image_obj.layers:
        # Create a list of dictionaries. Each dictionary represents one
        # layer as a SPDX package
        layer_dicts.append(get_layer_dict(layer))
    return layer_dicts
