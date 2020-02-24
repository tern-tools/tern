# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from abc import ABCMeta
from abc import abstractmethod


class Template(metaclass=ABCMeta):
    '''This is an abstract base class for reporting templates
    A specific type of template needs to be a subclass of this class
    methods:
        must implement:
            package: mappings for the properties under 'Package'
            layer: mappings for the properties under 'Layer'
            image: mappings for the properties under 'Image'
        should implement:
            notice: mappings for the properties under 'Notice'
            notice_origin: mappings for the properties under 'NoticeOrigin'
            origins: mappings for the properties under 'Origins' '''

    @abstractmethod
    def file_data(self):
        '''Must implement a mapping for 'FileData' class properties'''

    @abstractmethod
    def package(self):
        '''Must implement a mapping for 'Package' class properties'''

    @abstractmethod
    def image_layer(self):
        '''Must implement a mapping for 'ImageLayer' class properties'''

    @abstractmethod
    def image(self):
        '''Must implement a mapping for 'Image' class properties'''

    def notice(self):
        '''Should implement a mapping for 'Notice' class properties'''

    def notice_origin(self):
        '''Should implement a mapping for 'NoticeOrigin' class properties'''

    def origins(self):
        '''Should implement a mapping for 'Origins' class properties'''
