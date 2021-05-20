# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from abc import ABCMeta
from abc import abstractmethod


class Consume(metaclass=ABCMeta):
    """Base class for report consuming plugins"""
    @abstractmethod
    def consume(self, reports):
        """Ingest the contents of the list of files into an Image object or
        ImageLayer object according to the plugin type. Each plugin is
        responsible for implementing the reading and and assimilation of the
        report metadata"""
