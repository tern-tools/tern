# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.classes.template import Template


class SPDX(Template):
    '''This is the SPDX Template class
    It provides mappings for the SPDX tag-value document format'''

    def file_data(self):
        return {'name': 'FileName',
                'short_file_type': 'FileType'}

    def package(self):
        return {'name': 'PackageName',
                'version': 'PackageVersion',
                'pkg_license': 'PackageLicenseDeclared',
                'copyright': 'PackageCopyrightText',
                'download_url': 'PackageDownloadLocation'}

    def image_layer(self):
        return {'tar_file': 'PackageFileName'}

    def image(self):
        return {'name': 'PackageName',
                'tag': 'PackageVersion'}
