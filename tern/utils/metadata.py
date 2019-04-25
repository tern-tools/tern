# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Container metadata operations
"""

import os
import shutil
from tern.utils.constants import temp_folder


def clean_temp():
    '''Remove the temp directory'''
    temp_path = os.path.abspath(temp_folder)
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
