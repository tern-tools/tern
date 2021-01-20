# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helpers for layer information
Layers for SPDX act like a Package
"""
import logging
import os

from tern.formats.spdx import spdx_common
from tern.formats.spdx.spdxtagvalue import formats as spdx_formats
from tern.utils import constants
from tern.formats.spdx.spdxtagvalue import file_helpers as fhelpers
from tern.report import content

# global logger
logger = logging.getLogger(constants.logger_name)


def get_layer_comment(layer_obj):
    '''Return a PackageComment tag-value text block for a list of NoticeOrigin
    objects for the given layer object'''
    comment = ''
    # add any headers here
    if "headers" in layer_obj.extension_info.keys():
        for header in layer_obj.extension_info.get("headers"):
            comment += header + '\n'
    if not layer_obj.origins.is_empty():
        for notice_origin in layer_obj.origins.origins:
            comment = comment + content.print_notices(
                notice_origin, '', '\t')
        return spdx_formats.package_comment.format(comment=comment)
    return comment


def get_layer_package_relationships(layer_obj):
    '''Given a layer object, return the relationships of the layer
    objects to packages. This is usually of the form:
        layer SPDXIP CONTAINS package SPDXID'''
    block = ''
    layer_reference = spdx_common.get_layer_spdxref(layer_obj)
    for package in layer_obj.packages:
        block = block + spdx_formats.contains.format(
            outer=layer_reference,
            inner=spdx_common.get_package_spdxref(package)) + '\n'
    return block


def get_layer_prereq(curr_layer, prev_layer):
    '''Given the current layer and the previous layer, return the relationship
    between the current and previous layer. This should look like this:
        curr_layer HAS_PREREQUISITE prev_layer'''
    return spdx_formats.prereq.format(
        after=spdx_common.get_layer_spdxref(curr_layer),
        before=spdx_common.get_layer_spdxref(prev_layer))


def get_package_license_info_block(layer_obj):
    '''Given a layer object, return the SPDX document block with licenses
    from the files in the layer. Return an empty string if the files are
    not analyzed'''
    block = ''
    if layer_obj.files_analyzed:
        licenses = spdx_common.get_layer_licenses(layer_obj)
        if licenses:
            for lic in licenses:
                block += 'PackageLicenseInfoFromFiles: {}\n'.format(
                    spdx_common.get_license_ref(lic))
        else:
            block = 'PackageLicenseInfoFromFiles: NONE\n'
    return block


def get_layer_file_data_block(layer_obj, template):
    '''Given a layer object and the template object, return the SPDX document
    block with file data. Return an empty string if the files are not
    analyzed'''
    block = ''
    if layer_obj.files_analyzed:
        layer_checksum = spdx_common.get_layer_checksum(layer_obj)
        # insert a blank line in the beginning
        block += '\n'
        # some files are located in different places in the filesystem
        # they would occur as duplicates in this block
        # keep a list of previously printed file spdx-refs
        file_refs = set()
        # file data
        for filedata in layer_obj.files:
            # we use the layer checksum as the layer id
            file_ref = spdx_common.get_file_spdxref(filedata, layer_checksum)
            if file_ref not in file_refs:
                block += fhelpers.get_file_block(
                    filedata, template, layer_checksum) + '\n'
                file_refs.add(file_ref)
    return block


def get_layer_block(layer_obj, template):
    '''Given a layer object and its SPDX template mapping, return a SPDX
    document block for the layer. An image layer in SPDX behaves like a
    Package with relationships to the Packages within it. If the files
    are analyzed though, we just list the files in the block. The mapping
    should have keys:
        PackageFileName'''
    block = ''
    # Package Name
    block += 'PackageName: {}\n'.format(os.path.basename(layer_obj.tar_file))
    # Package SPDXID
    block += 'SPDXID: {}\n'.format(spdx_common.get_layer_spdxref(layer_obj))
    # Package File Name
    block += 'PackageFileName: {}\n'.format(layer_obj.tar_file)
    # Package Download Location (always NONE for layers)
    block += 'PackageDownloadLocation: NONE\n'
    # Files Analyzed
    if layer_obj.files_analyzed:
        # we need a package verification code
        block += 'FilesAnalyzed: true\n'
        block += 'PackageVerificationCode: {}\n'.format(
            spdx_common.get_layer_verification_code(layer_obj))
    else:
        block += 'FilesAnalyzed: false\n'
    # Package Checksum
    block += 'PackageChecksum: {}\n'.format(
        spdx_common.get_layer_checksum(layer_obj))
    # Package License Concluded (always NOASSERTION)
    block += 'PackageLicenseConcluded: NOASSERTION\n'
    # All licenses info from files if files_analyzed is true
    block += get_package_license_info_block(layer_obj)
    # Package License Declared (always NOASSERTION)
    block += 'PackageLicenseDeclared: NOASSERTION\n'
    # Package Copyright (always NOASSERTION)
    block += 'PackageCopyrightText: NOASSERTION\n'
    # Package comments if any
    block += get_layer_comment(layer_obj) + '\n'
    # put the file data here if files_analyzed is true
    block += get_layer_file_data_block(layer_obj, template)
    return block
