# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helper functions for image level JSON SPDX document dictionaries
Images for SPDX act like a Package
"""
from tern.formats.spdx import spdx_common
from tern.formats.spdx.spdxjson import formats as json_formats


def get_image_extracted_licenses(image_obj):
    '''Given an image_obj, return a unique list of extractedText dictionaries
    that contain all the file and package license key-value pairs for a
    LicenseRef and its corresponding plain text. The dictionaries will
    contain the following information:
        {
            "extractedText": "Plain text of license",
            "licenseId": "Corresponding LicenseRef"
        }'''

    unique_licenses = set()
    for layer in image_obj.layers:
        # Get all of the unique file licenses, if they exist
        unique_licenses.update(spdx_common.get_layer_licenses(layer))
        # Next, collect any package licenses not already accounted for
        for package in layer.packages:
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
    relationship between each layer "package" and the image "package".
    For SPDX JSON format this will typically look like:
    {
      "spdxElementId" : "SPDXRef-image",
      "relatedSpdxElement" : "SPDXRef-layer",
      "relationshipType" : "CONTAINS"
    }'''
    layer_relationships = []
    image_ref = spdx_common.get_image_spdxref(image_obj)

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
    return layer_relationships


def get_image_dict(image_obj, template):
    '''Given an image object and the template object for SPDX, return the
    SPDX document dictionary for the given image. For SPDX, the image is a
    package and hence follows the JSON spec for packages.
    The mapping for images should have these keys:
         name
         versionInfo
         downloadLocation'''
    image_dict = {}
    mapping = image_obj.to_dict(template)

    image_dict = {
        # describe the image as an SPDX package
        'name': mapping['PackageName'],
        'SPDXID': spdx_common.get_image_spdxref(image_obj),
        'versionInfo': mapping['PackageVersion'],
        'downloadLocation': 'NOASSERTION',  # always NOASSERTION
        'filesAnalyzed': 'false',  # always false
        'licenseConcluded': 'NOASSERTION',  # always NOASSERTION
        'licenseDeclared': 'NOASSERTION',  # always NOASSERTION
        'copyrightText': 'NOASSERTION'  # always NOASSERTION
    }

    return image_dict
