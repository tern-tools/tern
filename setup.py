#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from setuptools import setup
import unittest


def get_test_suite():
    return unittest.TestLoader().discover('tests', 'test_*.py')


setup(
    setup_requires=['pbr'],
    pbr=True,
    test_suite="setup.get_test_suite",
)
