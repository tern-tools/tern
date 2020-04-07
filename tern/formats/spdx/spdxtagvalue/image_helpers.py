# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helper functions for image level SPDX document blocks
Images for SPDX act like a Package
"""
from tern.formats.spdx import formats as spdx_formats
from tern.formats.spdx.spdxtagvalue import layer_helpers as lhelpers
from tern.formats.spdx.spdxtagvalue import package_helpers as phelpers


def get_image_spdxref(image_obj):
    '''Given the image object, return an SPDX reference ID'''
    # here we return the image name, tag and id
    return 'SPDXRef-{}'.format(image_obj.get_human_readable_id())


def get_image_layer_relationships(image_obj):
    '''Given the image object, return the relationships to the layers'''
    block = ''
    image_reference = get_image_spdxref(image_obj)
    for layer in image_obj.layers:
        block = block + spdx_formats.contains.format(
            outer=image_reference,
            inner=lhelpers.get_layer_spdxref(layer)) + '\n'
    return block


def get_image_block(image_obj, template):
    '''Given an image object and the template object for SPDX, return the
    SPDX document block for the given image. For SPDX, the image is a package
    and hence follows the spec for packages.
    The mapping for images should have these keys:
        PackageName
        PackageVersion
        PackageDownloadLocation'''
    block = ''
    mapping = image_obj.to_dict(template)
    # Package Name
    block += 'PackageName: {}\n'.format(mapping['PackageName'])
    # Package SPDXID
    block += 'SPDXID: {}\n'.format(get_image_spdxref(image_obj))
    # Package Version
    block += 'PackageVersion: {}\n'.format(mapping['PackageVersion'])
    # Package Download Location
    block += 'PackageDownloadLocation: {}\n'.format(
        mapping['PackageDownloadLocation'])
    # Files Analyzed (always false)
    block += 'FilesAnalyzed: false\n'
    # Concluded Package License (always NOASSERTION)
    block += 'PackageLicenseConcluded: NOASSERTION\n'
    # Declared Package License (always NOASSERTION)
    block += 'PackageLicenseDeclared: NOASSERTION\n'
    # Package Copyright Text (always NOASSERTION)
    block += 'PackageCopyrightText: NOASSERTION\n'
    # blank line
    block += '\n'
    # Since files are not analyzed within the image we move to relationships
    block += get_image_layer_relationships(image_obj) + '\n'
    # blank line
    block += '\n'
    # Describe each layer 'package' that the image contains
    for index, layer in enumerate(image_obj.layers):
        block += lhelpers.get_layer_block(
            layer, template, mapping['PackageDownloadLocation']) + '\n'
        # if the layer doesn't have files analyzed then print out the package
        # relationships
        if not layer.files_analyzed:
            # first print the layer's prerequisite relationship
            if index != 0:
                block += lhelpers.get_layer_prereq(
                    image_obj.layers[index], image_obj.layers[index - 1])
            # now print the layer's package relationships
            block += lhelpers.get_layer_package_relationships(layer)
            # blank line
            block += '\n'
            # print out each package's block
            block += lhelpers.get_layer_package_relationships(layer)
            # blank line
            block += '\n'
            # print out the license block for packages
            block += phelpers.get_package_license_block(layer.packages)
    return block
