# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
SPDX document generator
"""

import datetime

from tern.classes.templates.spdx import SPDX
from tern.utils.general import get_git_rev_or_version
from tern.report import formats as g_formats
from tern.report.spdxtagvalue import formats as spdx_formats


def get_document_namespace(image_obj):
    '''Given the image object, return a unique SPDX document uri.
    This is a combination of the human readable id from the image
    object and the tool name'''
    return spdx_formats.format(
        image_id=image_obj.get_human_readable_id(),
        version=get_git_rev_or_version()[1])


def get_package_spdxref(package_obj):
    '''Given the package object, return an SPDX reference ID'''
    return 'SPDXRef-{}'.format(package_obj.get_package_id())


def get_layer_spdxref(layer_obj):
    '''Given the layer object, return an SPDX reference ID'''
    # here we return the shortened diff_id of the layer
    return 'SPDXRef-{}'.format(layer_obj.diff_id[:10])


def get_image_spdxref(image_obj):
    '''Given the image object, return an SPDX reference ID'''
    # here we return the image name, tag and id
    return 'SPDXRef-{}'.format(image_obj.get_human_readable_id())


def get_document_block(image_obj):
    '''Return document related SPDX tag-values'''
    block = ''
    block = spdx_formats.spdx_version + '\n'
    block = block + spdx_formats.data_license + '\n'
    block = block + spdx_formats.spdx_id + '\n'
    block = block + spdx_formats.document_name.format(
        image_name=image_obj.get_human_readable_id()) + '\n'
    block = block + get_document_namespace(image_obj)
    block = block + spdx_formats.license_list_version
    block = block + spdx_formats.creator.format(
        version=get_git_rev_or_version()[1])
    block = block + spdx_formats.created.format(
        timestamp=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))


def get_image_comment(image_obj_origins):
    '''Return a PackageComment tag-value text block for the image level
    notices'''


def get_layer_comment(layer_obj_origins):
    '''Return a PackageComment tag-value text block for the layer level
    notices'''


def get_package_comment(package_obj_origins):
    '''Return a PackageComment tag-value text block for package level
    notices'''


def get_image_block(image_dict, image_origins):
    '''Given the image dictionary and the list of notices for the image,
    return the SPDX tag-value for image level information'''


def get_layer_block(layer_dict, layer_origins, prev_layer_SPDX=None):
    '''Given the layer dictionary, the list of notices for the layer and
    the previous layer's SPDXref if there is a previous layer, return the
    SPDX tag-value for the layer level information'''


def get_package_block(package_dict, package_origins):
    '''Given the package dictionary, and the list of notices for the package,
    return the SPDX tag-value for the package level information'''


def generate(image_obj):
    '''Given an Image object, generate an SPDX document
    The whole document should be stored in a string which can be written
    to a file using the write_report function in report.py
    First convert the image object into a dictionary. The dictionary
    should be in this form:
        image:{
          origins: [...]
          layers: [
            {origins: [...],
             packages: [
               {origins: [...], package1: {...}},
               {origins: [...], package2: {...}}...]}, ...]}
    Then convert this into a flat format starting from top to bottom
    So:
        ## image
        List all the tag-values here
        make a PackageComment: <text> </text>

        ## relationships
        spdx-ref CONTAINS layer1
        spdx-ref CONTAINS layer2
        ...

        ## layer1
        List all the tag-values here
        make a PackageComment here

        # relationships
        spdx-ref CONTAINS package1
        spdx-ref CONTAINS package2
        ....

        # layer2
        tag-values
        PackageComment

        # relationships
        spdx-ref HAS_PREREQUISITE layer1
        spdx-ref CONTAINS package3
        spdx-ref CONTAINS package4

        ....

        # package1
        tag-values
        PackageComment

        # package2

        # package3

        # package4


    Everything in Origins can be in a tag-value format as
    PackageComment: <text> </text>

    For the sake of SPDX, an image is a 'Package' which 'CONTAINS'
    each layer which is also a 'Package' which 'CONTAINS' the real Package'''
    report = ''
    template = SPDX()
    spdx_dict = image_obj.to_dict(template)
    # first part is the document tag-value
    # this doesn't change at all
    report = report + get_document_block()
    # this part is the image part and needs
    # the image object
    report = report + get_image_block(spdx_dict, image_obj.origins.origins)
    # Add the layer part for each layer
    for index, layer_dict in enumerate(spdx_dict['layers']):
        if index == 0:
            # no previous layer dependencies
            report = report + get_layer_block(
                layer_dict,
                image_obj.layers[index].origins.origins)
        else:
            # block should contain previous layer dependency
            report = report + get_layer_block(
                layer_dict,
                image_obj.layers[index].origins.origins,
                get_layer_spdxref(image_obj.layers[index - 1]))
    # Add the package part for each package
    for i, _ in enumerate(spdx_dict['layers']):
        for j, package_dict in enumerate(spdx_dict['layers'][i]['packages']):
            report = report + get_package_block(
                package_dict, image_obj.layers[i].packages[j].origins.origins)
    return report
