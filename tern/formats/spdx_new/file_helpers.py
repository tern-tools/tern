# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 VMWare, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
File level helpers for SPDX document generator
"""
from datetime import datetime
from typing import List

from spdx_tools.spdx.model import File as SpdxFile, SpdxNone, SpdxNoAssertion, Checksum, ChecksumAlgorithm

from tern.classes.file_data import FileData
from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.classes.template import Template
from tern.formats.spdx_new.layer_helpers import get_layer_checksum
from tern.formats.spdx_new.general_helpers import get_package_license_declared, get_file_spdxref


def get_spdx_file_list_from_layer(layer_obj: ImageLayer, template: Template, timestamp: datetime) -> List[SpdxFile]:
    """Given a layer object and the SPDX template mapping, return a list
    of SPDX Files for each file in the layer"""
    spdx_files: List[SpdxFile] = []
    file_refs = set()
    for filedata in layer_obj.files:
        # we do not know the layer's id, so we will use the timestamp instead
        file_ref = get_file_spdxref(filedata, str(timestamp))
        if file_ref not in file_refs:
            spdx_files.append(get_spdx_file_from_filedata(filedata, template, str(timestamp)))
            file_refs.add(file_ref)
    return spdx_files


def get_spdx_file_list_from_image(image_obj: Image, template: Template) -> List[SpdxFile]:
    '''Given an image_obj object, and the SPDX template mapping, return a list
    of SPDX dictionary representations for each file in each layer of the
    image.'''
    spdx_files: List[SpdxFile] = []

    # use file refs to keep track of duplicate files that may be located
    # in different places in the filesystem
    file_refs = set()
    for layer in image_obj.layers:
        if layer.files_analyzed:
            layer_checksum_value = get_layer_checksum(layer).value
            for filedata in layer.files:
                # we use the layer checksum as the layer id
                file_ref = get_file_spdxref(filedata, layer_checksum_value)
                if file_ref not in file_refs:
                    spdx_files.append(get_spdx_file_from_filedata(filedata, template, layer_checksum_value))
                    file_refs.add(file_ref)
    return spdx_files


def get_spdx_file_from_filedata(filedata: FileData, template: Template, layer_id: str) -> SpdxFile:
    """Given a FileData object and its SPDX template mapping, return an
    SPDX representation of the file. A layer_id is used to
    distinguish copies of the same file occurring in different places in the
    image"""
    mapping = filedata.to_dict(template)

    if filedata.licenses:
        # Add the license expression to the list if it is a valid SPDX
        # identifier; otherwise, add the LicenseRef
        license_info_in_file = [get_package_license_declared(lic) for lic in set(filedata.licenses)]
    else:
        license_info_in_file = [SpdxNone()]

    file_notice = get_file_notice(filedata)
    file_comment = get_file_comment(filedata)
    file_contributors = get_file_contributors(filedata)

    return SpdxFile(
        spdx_id=get_file_spdxref(filedata, layer_id),
        name=mapping['FileName'],
        checksums=[get_file_checksum(filedata)],
        license_concluded=SpdxNoAssertion(),  # we don't provide this
        copyright_text=SpdxNoAssertion(),     # we don't know this
        file_types=[mapping['FileType']] if mapping['FileType'] else None,
        license_info_in_file=license_info_in_file,
        notice=file_notice if file_notice else None,
        comment=file_comment if file_comment else None,
        contributors=file_contributors if file_contributors else None,
    )


def get_file_checksum(filedata: FileData) -> Checksum:
    """Given a FileData object, return the checksum required by SPDX.
    Currently, the spec requires a SHA1 checksum"""
    return Checksum(ChecksumAlgorithm.SHA1, filedata.get_checksum('sha1'))


def get_file_notice(filedata: FileData) -> str:
    """Return a formatted string with all copyrights found in a file. Return
    an empty string if there are no copyrights"""
    notice = ''
    for cp in filedata.copyrights:
        notice = notice + cp + '\n'
    return notice


def get_file_comment(filedata: FileData) -> str:
    """Return a formatted comment string with all file level notices. Return
    an empty string if no notices are present"""
    comment = ''
    for origin in filedata.origins.origins:
        comment = comment + f'{origin.origin_str}:' + '\n'
        for notice in origin.notices:
            comment = comment + \
                f'{notice.level}: {notice.message}' + '\n'
    return comment


def get_file_contributors(filedata: FileData) -> List[str]:
    """The SPDX spec allows for an optional list of file contributors.
    If there are any authors found in the file, return a list of authors.
    If empty, return an empty list"""
    contributors = []
    for author in filedata.authors:
        contributors.append(author)
    return contributors
