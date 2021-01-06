# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from abc import ABCMeta
from abc import abstractmethod


class Generate(metaclass=ABCMeta):
    '''Base class for report plugins'''
    @abstractmethod
    def generate(self, image_obj_list, print_inclusive=False):
        '''Format the report according to the plugin style.
        Each subclass is responsible for their own formatting.'''
