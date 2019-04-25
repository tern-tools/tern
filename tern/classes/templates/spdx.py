# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

from tern.classes.template import Template


class SPDXTagValue(Template):
    '''This is the SPDX Template class
    It provides mappings for the SPDX tag-value document format'''

    def package(self):
        return {'name': 'PackageName',
                'version': 'PackageVersion',
                'license': 'PackageLicenseDeclared'}

    def image_layer(self):
        return {'diff_id': 'PackageName',
                'fs_hash': 'PackageChecksum'}

    def image(self):
        return {'name': 'PackageName',
                'tag': 'PackageVersion',
                'id': 'PackageChecksum'}
