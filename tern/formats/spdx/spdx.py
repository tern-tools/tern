# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.classes.template import Template


class SPDX(Template):
    '''This is the SPDX Template class
    It provides mappings for the SPDX tag-value document format'''

    def package(self):
        return {'name': 'PackageName',
                'version': 'PackageVersion',
                'pkg_license': 'PackageLicenseDeclared',
                'copyright': 'PackageCopyrightText',
                'download_url': 'PackageDownloadLocation'}

    def image_layer(self):
        # TODO: hash_type should be added in the class property
        # not hardcoded here
        return {'diff_id': 'PackageName',
                'fs_hash': 'PackageChecksum: SHA256'}

    def image(self):
        return {'name': 'PackageName',
                'tag': 'PackageVersion',
                'repotag': 'PackageDownloadLocation'}
