# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helper functions for image level SPDX document blocks
Images for SPDX act like a Package
"""
from tern.formats.spdx.spdxtagvalue import formats as spdx_formats
from tern.formats.spdx.spdxtagvalue import layer_helpers as lhelpers
from tern.formats.spdx.spdxtagvalue import package_helpers as phelpers
from tern.formats.spdx import spdx_common


def get_image_layer_relationships(image_obj):
    '''Given the image object, return the relationships to the layers'''
    block = ''
    image_reference = spdx_common.get_image_spdxref(image_obj)
    for layer in image_obj.layers:
        block = block + spdx_formats.contains.format(
            outer=image_reference,
            inner=lhelpers.spdx_common.get_layer_spdxref(layer)) + '\n'
    return block


def get_image_packages_block(image_obj, template):
    '''Given the image object and its template, return the list of packages
    in the image in SPDX format. The spec requires unique package references
    to identify each package found in the image.'''
    block = ''
    package_refs = set()
    for layer in image_obj.layers:
        for package in layer.packages:
            pkg_ref = spdx_common.get_package_spdxref(package)
            if pkg_ref not in package_refs:
                block += phelpers.get_package_block(package, template) + '\n'
                package_refs.add(pkg_ref)
    return block


def get_image_packages_license_block(image_obj):
    '''Given the image object, get all the the licenses found for packages
    in the image. The SPDX spec requires that each license reference be
    unique for the document'''
    block = ''
    licenses = set()
    for layer in image_obj.layers:
        for package in layer.packages:
            if package.pkg_license:
                licenses.add(package.pkg_license)
    for lic in licenses:
        block += spdx_formats.license_id.format(
            license_ref=spdx_common.get_license_ref(lic)) + '\n'
        block += spdx_formats.extracted_text.format(orig_license=lic) + '\n'
    return block


def get_image_file_license_block(image_obj):
    '''Given the image object, get all the licenses found for the files
    in the image. We will make use of some helper functions from the layer
    and file helpers'''
    block = ''
    licenses = set()
    for layer in image_obj.layers:
        if layer.files_analyzed:
            for lic in spdx_common.get_layer_licenses(layer):
                licenses.add(lic)
    for lic in licenses:
        block += spdx_formats.license_id.format(
            license_ref=spdx_common.get_license_ref(lic)) + '\n'
        block += spdx_formats.extracted_text.format(orig_license=lic) + '\n'
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
    block += 'SPDXID: {}\n'.format(spdx_common.get_image_spdxref(image_obj))
    # Package Version
    block += 'PackageVersion: {}\n'.format(mapping['PackageVersion'])
    # Package Download Location (always NOASSERTION)
    block += 'PackageDownloadLocation: NOASSERTION\n'
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
        block += lhelpers.get_layer_block(layer, template) + '\n'
        # print layer relationship to previous layer if there is one
        if index != 0:
            block += lhelpers.get_layer_prereq(
                image_obj.layers[index], image_obj.layers[index - 1]) + '\n'
        # if the layer has packages, print out the relationships
        if layer.packages:
            block += lhelpers.get_layer_package_relationships(layer) + '\n'
    # print out all the packages if they are known
    pkg_block = get_image_packages_block(image_obj, template)
    if pkg_block:
        # add a blank line before adding the package block
        block += pkg_block + '\n'
        # print out the license block for packages
        block += get_image_packages_license_block(image_obj)
    block += get_image_file_license_block(image_obj)
    return block
