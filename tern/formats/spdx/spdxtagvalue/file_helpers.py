# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
File level helpers for SPDX tag-value document generator
"""


# basic functions
def get_file_spdxref(filedata):
    '''Given a FileData object, return a unique identifier for the SPDX
    document. According to the spec, this should be of the form: SPDXRef-<id>
    We will return a combination of the file name and checksum'''
    return 'SPDXRef-{}'.format(filedata.name + filedata.checksum[:7])


def get_file_checksum(filedata):
    '''Given a FileData object, return the checksum required by SPDX.
    This should be of the form: <checksum_type>: <checksum>'''
    return '{}: {}'.format(filedata.checksum_type.upper(), filedata.checksum)


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


def get_file_notice(filedata):
    '''Return a formatted string with all copyrights found in a file. Return
    an empty string if there are no copyrights'''
    notice = ''
    for copyright in filedata.copyrights:
        notice = notice + copyright + '\n'
    return notice


# formatting functions
def get_license_info_block(filedata):
    '''The SPDX spec asks to list the license expressions found in a file
    using the format: LicenseInfoInFile: <license expression>. If the license
    expressions list is empty, this should be "NONE"'''
    block = ''
    if not filedata.license_expressions:
        block = 'LicenseInfoInFile: NONE\n'
    else:
        for le in filedata.license_expressions:
            block = block + 'LicenseInfoInFile: {}'.format(le) + '\n'
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
def get_file_block(filedata, template):
    '''Given a FileData object, and the SPDX template mapping, return a SPDX
    document block for the file. The mapping should have only FileName and
    FileType keys'''
    block = ''
    mapping = filedata.to_dict(template)
    # File Name
    block = block + 'FileName: {}'.format(mapping['FileName']) + '\n'
    # SPDX ID
    block = block + 'SPDXID: {}'.format(get_file_spdxref(filedata)) + '\n'
    # File Type
    block = block + 'FileType: {}'.format(mapping['FileType']) + '\n'
    # File checksum
    block = block + 'FileChecksum: {}'.format(get_file_checksum(filedata)) + \
        '\n'
    # Concluded license - we won't provide this
    block = block + 'LicenseConcluded: NOASSERTION' + '\n'
    # License info in file
    block = block + get_license_info_block(filedata)
    # File copyright text - we don't know this
    block = block + 'FileCopyrightText: NOASSERTION' + '\n'
    # File comment - we add this only if there is a comment
    comment = get_file_comment(filedata)
    if comment:
        block = block + 'FileComment: <text>\n' + comment + '</text>' + '\n'
    # File Notice - we add this only if there is a notice
    notice = get_file_notice(filedata)
    if notice:
        block = block + 'FileNotice: <text>\n' + notice + '</text>' + '\n'
    # File Contributor - we add this only if there are contributors
    contributors = get_file_contributor_block(filedata)
    if contributors:
        block = block + contributors
    return block
