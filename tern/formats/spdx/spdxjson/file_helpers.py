# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
File level helpers for SPDX JSON document generator
"""

from tern.formats.spdx import spdx_common


def get_file_contributors(filedata):
    '''The SPDX spec allows for an optional list of file contributors.
    If there are any authors found in the file, return a list of authors.
    If empty, return an empty list'''
    contributors = []
    for author in filedata.authors:
        contributors.append(author)
    return contributors


def get_file_dict(filedata, template, layer_id):
    '''''Given a FileData object and its SPDX template mapping, return a
    SPDX JSON dictionary representation of the file. A layer_id is used to
    distinguish copies of the same file occuring in different places in the
    image'''
    mapping = filedata.to_dict(template)
    file_dict = {
        'fileName': mapping['FileName'],
        'SPDXID': spdx_common.get_file_spdxref(filedata, layer_id),
        'checksums': [{
            'algorithm':
                spdx_common.get_file_checksum(filedata).split(': ')[0],
            'checksumValue':
                spdx_common.get_file_checksum(filedata).split(': ')[1]
        }],
        'licenseConcluded': 'NOASSERTION',  # we don't provide this
        'copyrightText': 'NOASSERTION'  # we don't know this
    }

    # Some files may not have a fileType available
    if mapping['FileType']:
        file_dict['fileTypes'] = [mapping['FileType']]

    if not filedata.licenses:
        file_dict['licenseInfoInFiles'] = ['NONE']
    else:
        file_license_refs = []
        for lic in spdx_common.get_file_licenses(filedata):
            # Add the LicenseRef to the list instead of license expression
            file_license_refs.append(spdx_common.get_license_ref(lic))
        file_dict['licenseInfoInFiles'] = file_license_refs

    # We only add this if there is a notice
    file_notice = spdx_common.get_file_notice(filedata)
    if file_notice:
        file_dict['noticeText'] = file_notice

    # We only add this if there is a comment
    file_comment = spdx_common.get_file_comment(filedata)
    if file_comment:
        file_dict['comment'] = file_comment

    # We only add this if there are contributors
    file_contributors = get_file_contributors(filedata)
    if file_contributors:
        file_dict['fileContributors'] = file_contributors

    return file_dict


def get_files_list(image_obj, template):
    '''Given a image_obj object, and the SPDX template mapping, return a list
    of SPDX dictionary representations for each file in each layer of the
    image.'''
    file_dicts = []

    # use file refs to keep track of duplicate files that may be located
    # in different places in the filesystem
    file_refs = set()
    for layer in image_obj.layers:
        if layer.files_analyzed:
            layer_checksum = spdx_common.get_layer_checksum(layer)
            for filedata in layer.files:
                # we use the layer checksum as the layer id
                file_ref = spdx_common.get_file_spdxref(
                    filedata, layer_checksum)
                if file_ref not in file_refs:
                    file_dicts.append(get_file_dict(
                        filedata, template, layer_checksum))
                    file_refs.add(file_ref)
    return file_dicts
