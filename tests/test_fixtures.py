# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Objects to use for testing
"""

from tern.classes.package import Package
from tern.classes.image_layer import ImageLayer
from tern.classes.image import Image
from tern.classes.template import Template


class TestImage(Image):
    def __init__(self, id):
        super().__init__(id)

    def load_image(self):
        l1 = ImageLayer('123abc', 'path/to/tar')
        l1.add_package(Package('p1'))
        l1.add_package(Package('p2'))
        self._layers.append(l1)


class TestTemplate1(Template):
    '''Template with no origins mapping'''
    def package(self):
        return {'name': 'package.name',
                'version': 'package.version',
                'pkg_license': 'package.license'}

    def image_layer(self):
        return {'diff_id': 'layer.diff',
                'tar_file': 'layer.tarfile',
                'packages': 'layer.packages'}

    def image(self):
        return {'image_id': 'image.id',
                'layers': 'image.layers'}


class TestTemplate2(Template):
    '''Template with origins mapping'''
    def package(self):
        mapping = {'name': 'package.name',
                   'version': 'package.version',
                   'pkg_license': 'package.license',
                   'src_url': 'package.url'}
        # we update the mapping with another defined mapping
        mapping.update(self.origins())
        return mapping

    def image_layer(self):
        mapping = {'diff_id': 'layer.diff',
                   'tar_file': 'layer.tarfile',
                   'packages': 'layer.packages'}
        # we update the mapping with another defined mapping
        mapping.update(self.origins())
        return mapping

    def image(self):
        mapping = {'image_id': 'image.id',
                   'layers': 'image.layers'}
        # we update the mapping with another defined mapping
        mapping.update(self.origins())
        return mapping

    def notice(self):
        return {'level': 'note.level',
                'message': 'note.message'}

    def notice_origin(self):
        return {'origin_str': 'note.source',
                'notices': 'note.messages'}

    def origins(self):
        return {'origins': 'notes'}
