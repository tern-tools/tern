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

# global logger
logger = logging.getLogger(constants.logger_name)


def get_layer_spdxref(layer_obj):
    '''Given the layer object, return an SPDX reference ID'''
    # here we return the shortened diff_id of the layer
    return 'SPDXRef-{}'.format(layer_obj.diff_id[:10])


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


def get_file_license_expressions(layer_obj):
    '''Return a list of unique license expressions from the files analyzed
    in the layer object. It is assumed that the files were analyzed and
    there should be some license expressions. If there are not, an empty list
    is returned'''
    license_expressions = set()
    for filedata in layer_obj.files:
        if filedata.license_expressions:
            for le in filedata.license_expressions:
                license_expressions.add(le)
    return list(license_expressions)


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
    # All licenses info from files
    if layer_obj.files_analyzed:
        license_expressions = get_file_license_expressions(layer_obj)
        if license_expressions:
            for le in license_expressions:
                block += 'PackageLicenseInfoFromFiles: {}\n'.format(le)
        else:
            block += 'PackageLicenseInfoFromFiles: NONE\n'
    # Package License Declared (always NOASSERTION)
    block += 'PackageLicenseDeclared: NOASSERTION\n'
    # Package Copyright (always NOASSERTION)
    block += 'PackageCopyrightText: NOASSERTION\n'
    # put the file data here if files_analyzed is true
    if layer_obj.files_analyzed:
        # blank new line
        block += '\n'
        # file data
        for filedata in layer_obj.files:
            block += fhelpers.get_file_block(filedata, template) + '\n'
    return block
