#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import os
import sys

from tern import Version
from setuptools.command.install import install
from setuptools import setup


class VerifyVersion(install):
    """Run a custom verify command"""
    description = "Verify that the git tag matches current release version."

    def run(self):
        tag = os.getenv('CIRCLE_TAG')
        if tag.lstrip('v') != Version:
            info = "Git tag {0} does not match Tern version {1}".format(
                tag, Version)
            sys.exit(info)


setup(
    setup_requires=['pbr'],
    pbr=True,
    test_suite="tests.runtests",
    cmdclass={
        "verify": VerifyVersion,
    }
)
