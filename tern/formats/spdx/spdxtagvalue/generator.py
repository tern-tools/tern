# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
SPDX document generator
"""

import datetime
import logging

from tern.formats.spdx.spdx import SPDX
from tern.formats.spdx import spdx_common
from tern.utils.general import get_git_rev_or_version
from tern.utils import constants
from tern.formats.spdx.spdxtagvalue import formats as spdx_formats
from tern.formats.spdx.spdxtagvalue import image_helpers as mhelpers
from tern.formats import generator


# global logger
logger = logging.getLogger(constants.logger_name)


def get_document_namespace(image_obj):
    '''Given the image object, return a unique SPDX document uri.
    This is a combination of the tool name and version, the image name
    and the uuid'''
    return spdx_formats.document_namespace.format(
        version=get_git_rev_or_version()[1], image=image_obj.name,
        uuid=spdx_common.get_uuid())


def get_document_block(image_obj):
    '''Return document related SPDX tag-values'''
    block = spdx_formats.spdx_version + '\n'
    block = block + spdx_formats.data_license + '\n'
    block = block + spdx_formats.spdx_id + '\n'
    block = block + spdx_formats.document_name.format(
        image_name=image_obj.name) + '\n'
    block = block + get_document_namespace(image_obj) + '\n'
    block = block + spdx_formats.license_list_version + '\n'
    block = block + spdx_formats.creator.format(
        version=get_git_rev_or_version()[1]) + '\n'
    block = block + spdx_formats.created.format(
        timestamp=datetime.datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%SZ")) + '\n'
    block = block + spdx_formats.document_comment + '\n'
    return block


class SpdxTagValue(generator.Generate):
    def generate(self, image_obj_list):
        '''Generate an SPDX document
        WARNING: This assumes that the list consists of one image or the base
        image and a stub image, in which case, the information in the stub
        image is not applicable in the SPDX case as it is an empty image
        object with no metadata as nothing got built.
        The whole document should be stored in a string which can be written
        to a file using the write_report function in report.py
        First convert the image object into a dictionary. The dictionary
        should be in this form:
            image:{
              origins: [...]
              layers: [
                {origins: [...],
                 packages: [
                   {name: package1,..origins: [...]},
                   {name: package2,..origins: [...]},..],
                 files: [
                   {name: file1,..origins: [...]},
                   {name: file2,..origins: [...]},..]}
                   ...]}
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

            ## if layer1 has files analyzed
            ### extra package info here
            ### file level information here

            ## if not then package relationships
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

        For the sake of SPDX, an image is a 'Package' which 'CONTAINS' each
        layer which is also a 'Package' which 'CONTAINS' the real Package'''
        logger.debug("Generating SPDX document...")
        report = ''

        # we still don't know how SPDX documents could represent multiple
        # images. Hence we will assume only one image is analyzed and the
        # input is a list of length 1
        image_obj = image_obj_list[0]
        template = SPDX()

        # first part is the document tag-value
        # this doesn't change at all
        report += get_document_block(image_obj) + '\n'

        # this is the image part
        # this will bring in layer and package information
        report += mhelpers.get_image_block(image_obj, template) + '\n'

        return report
