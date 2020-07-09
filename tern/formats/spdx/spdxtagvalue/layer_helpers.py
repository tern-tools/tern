# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helpers for layer information
Layers for SPDX act like a Package
"""
import hashlib
import logging
import os

from tern.formats.spdx import formats as spdx_formats
from tern.utils import constants
from tern.formats.spdx.spdxtagvalue import file_helpers as fhelpers
from tern.formats.spdx.spdxtagvalue import package_helpers as phelpers
from tern.report import content

# global logger
logger = logging.getLogger(constants.logger_name)


def get_layer_spdxref(layer_obj):
    '''Given the layer object, return an SPDX reference ID'''
    # here we return the shortened diff_id of the layer
    return 'SPDXRef-{}'.format(layer_obj.diff_id[:10])


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
    layer_reference = get_layer_spdxref(layer_obj)
    for package in layer_obj.packages:
        block = block + spdx_formats.contains.format(
            outer=layer_reference,
            inner=phelpers.get_package_spdxref(package)) + '\n'
    return block


def get_layer_prereq(curr_layer, prev_layer):
    '''Given the current layer and the previous layer, return the relationship
    between the current and previous layer. This should look like this:
        curr_layer HAS_PREREQUISITE prev_layer'''
    return spdx_formats.prereq.format(
        after=get_layer_spdxref(curr_layer),
        before=get_layer_spdxref(prev_layer))


def get_layer_verification_code(layer_obj):
    '''Calculate the verification code from the files in an image layer. This
    assumes that layer_obj.files_analyzed is True. The implementation follows
    the algorithm in the SPDX spec v 2.1 which requires SHA1 to be used to
    calculate the checksums of the file and the final verification code'''
    sha1_list = []
    for filedata in layer_obj.files:
        filesha = filedata.get_checksum('sha1')
        if not filesha:
            # we cannot create a verification code, hence file generation
            # is aborted
            logger.critical(
                'File %s does not have a sha1 checksum. Failed to generate '
                'a SPDX tag-value report', filedata.path)
            return None
        sha1_list.append(filesha)
    sha1_list.sort()
    sha1s = ''.join(sha1_list)
    return hashlib.sha1(sha1s.encode('utf-8')).hexdigest()  # nosec


def get_layer_checksum(layer_obj):
    '''Return a SPDX formatted checksum value. It should be of the form:
        checksum_type: <checksum>'''
    return '{}: {}'.format(layer_obj.checksum_type.upper(), layer_obj.checksum)


def get_layer_licenses(layer_obj):
    '''Return a list of unique licenses from the files analyzed
    in the layer object. It is assumed that the files were analyzed and
    there should be some license expressions. If there are not, an empty list
    is returned'''
    licenses = set()
    for filedata in layer_obj.files:
        # we will use the SPDX license expressions here as they will be
        # valid SPDX license identifiers
        if filedata.licenses:
            for lic in fhelpers.get_file_licenses(filedata):
                licenses.add(lic)
    return list(licenses)


def get_package_license_info_block(layer_obj):
    '''Given a layer object, return the SPDX document block with licenses
    from the files in the layer. Return an empty string if the files are
    not analyzed'''
    block = ''
    if layer_obj.files_analyzed:
        licenses = get_layer_licenses(layer_obj)
        if licenses:
            for lic in licenses:
                block += 'PackageLicenseInfoFromFiles: {}\n'.format(
                    spdx_formats.get_license_ref(lic))
        else:
            block = 'PackageLicenseInfoFromFiles: NONE\n'
    return block


def get_layer_file_data_block(layer_obj, template):
    '''Given a layer object and the template object, return the SPDX document
    block with file data. Return an empty string if the files are not
    analyzed'''
    block = ''
    if layer_obj.files_analyzed:
        layer_checksum = get_layer_checksum(layer_obj)
        # insert a blank line in the beginning
        block += '\n'
        # some files are located in different places in the filesystem
        # they would occur as duplicates in this block
        # keep a list of previously printed file spdx-refs
        file_refs = set()
        # file data
        for filedata in layer_obj.files:
            # we use the layer checksum as the layer id
            file_ref = fhelpers.get_file_spdxref(filedata, layer_checksum)
            if file_ref not in file_refs:
                block += fhelpers.get_file_block(
                    filedata, template, layer_checksum) + '\n'
                file_refs.add(file_ref)
    return block


def get_layer_block(layer_obj, template, image_loc=''):
    '''Given a layer object and its SPDX template mapping, return a SPDX
    document block for the layer. An image layer in SPDX behaves like a
    Package with relationships to the Packages within it. If the files
    are analyzed though, we just list the files in the block. The mapping
    should have keys:
        PackageFileName
    We also pass the image location as optional for where the layers were
    downloaded from. Registries can be implemented as distributed storage
    or images can be stored as whole tarballs. Either way, the layers
    would be downloaded along with the image.'''
    block = ''
    mapping = layer_obj.to_dict(template)
    # Package Name
    block += 'PackageName: {}\n'.format(os.path.basename(layer_obj.tar_file))
    # Package SPDXID
    block += 'SPDXID: {}\n'.format(get_layer_spdxref(layer_obj))
    # Package File Name
    block += 'PackageFileName: {}\n'.format(layer_obj.tar_file)
    # Package Download Location
    if image_loc:
        block += 'PackageDownloadLocation: {}\n'.format(
            mapping['PackageFileName'])
    else:
        block += 'PackageDownloadLocation: NONE\n'
    # Files Analyzed
    if layer_obj.files_analyzed:
        # we need a package verification code
        block += 'FilesAnalyzed: true\n'
        block += 'PackageVerificationCode: {}\n'.format(
            get_layer_verification_code(layer_obj))
    else:
        block += 'FilesAnalyzed: false\n'
    # Package Checksum
    block += 'PackageChecksum: {}\n'.format(get_layer_checksum(layer_obj))
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
