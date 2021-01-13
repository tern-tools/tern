# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
File level helpers for SPDX tag-value document generator
"""

from tern.formats.spdx import spdx_common


def get_file_comment(filedata):
    '''Return a formatted comment string with all file level notices. Return
    an empty string if no notices are present'''
    comment = ''
    for origin in filedata.origins.origins:
        comment = comment + '{}:'.format(origin.origin_str) + '\n'
        for notice in origin.notices:
            comment = comment + \
                '{}: {}'.format(notice.level, notice.message) + '\n'
    return comment


# formatting functions
def get_license_info_block(filedata):
    '''The SPDX spec asks to list of SPDX license identifiers or license
    reference IDs using the format: LicenseInfoInFile: <license ref>.
    In this case, we do not know if we are collecting SPDX license identifiers
    or license strings or something else. So we will create license refs here.
    If the licenses list is empty we will report NONE'''
    block = ''
    if not filedata.licenses:
        block = 'LicenseInfoInFile: NONE\n'
    else:
        for lic in spdx_common.get_file_licenses(filedata):
            block = block + 'LicenseInfoInFile: {}'.format(
                spdx_common.get_license_ref(lic)) + '\n'
    return block


def get_file_contributor_block(filedata):
    '''The SPDX spec allows for an optional block listing file contributors.
    If there are any authors found in the file, return a formatted SPDX text
    block with the list of authors. If empty, return an empty string'''
    block = ''
    for author in filedata.authors:
        block = block + 'FileContributor: {}'.format(author) + '\n'
    return block


# full file block
def get_file_block(filedata, template, layer_id):
    '''Given a FileData object, and the SPDX template mapping, return a SPDX
    document block for the file. The mapping should have only FileName and
    FileType keys. A layer id is used to distinguish copies of the
    same file occuring in different places in the image'''
    block = ''
    mapping = filedata.to_dict(template)
    # File Name
    block = block + 'FileName: {}'.format(mapping['FileName']) + '\n'
    # SPDX ID
    block = block + 'SPDXID: {}'.format(
        spdx_common.get_file_spdxref(filedata, layer_id)) + '\n'
    # File Type
    block = block + 'FileType: {}'.format(mapping['FileType']) + '\n'
    # File checksum
    block = block + 'FileChecksum: {}'.format(
        spdx_common.get_file_checksum(filedata)) + '\n'
    # Concluded license - we won't provide this
    block = block + 'LicenseConcluded: NOASSERTION' + '\n'
    # License info in file
    block = block + get_license_info_block(filedata)
    # File copyright text - we don't know this
    block = block + 'FileCopyrightText: NOASSERTION' + '\n'
    # File comment - we add this only if there is a comment
    comment = spdx_common.get_file_comment(filedata)
    if comment:
        block = block + 'FileComment: <text>\n' + comment + '</text>' + '\n'
    # File Notice - we add this only if there is a notice
    notice = spdx_common.get_file_notice(filedata)
    if notice:
        block = block + 'FileNotice: <text>\n' + notice + '</text>' + '\n'
    # File Contributor - we add this only if there are contributors
    contributors = get_file_contributor_block(filedata)
    if contributors:
        block = block + contributors
    return block
