# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
SPDX document generator
"""

from tern.classes.templates.spdx import SPDX


def generate(image_obj):
    '''Given an Image object, generate an SPDX document
    The whole document should be stored in a string which can be written
    to a file using the write_report function in report.py
    First convert the image object into a dictionary. The dictionary
    should be in this form:
        image:{
          origins: [...]
          layers: [
            {origins: [...],
             packages: [
               {origins: [...], package1: {...}},
               {origins: [...], package2: {...}}...]}, ...]}
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

        # relationships
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

        # package2

        # package3

        # package4


    Everything in Origins can be in a tag-value format as
    PackageComment: <text> </text>

    For the sake of SPDX, an image is a 'Package' which 'CONTAINS'
    each layer which is also a 'Package' which 'CONTAINS' the real Package'''
    template = SPDX()
    spdx_dict = image_obj.to_dict(template)
    return spdx_dict
