# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from abc import ABCMeta
from abc import abstractmethod


class Executor(metaclass=ABCMeta):
    '''Base class for the external tool executor'''
    @abstractmethod
    def execute(self, image_obj, redo=False):
        '''Return a string consisting of the command the tool should execute
        for the container image filesystem. Allow for the filesystem directory
        to be incorporated in the command'''

    @abstractmethod
    def execute_layer(self, image_layer, redo=False):
        '''...'''
