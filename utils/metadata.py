'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import os
import shutil
from utils.constants import temp_folder

'''
Container metadata operations
'''


def clean_temp():
    '''Remove the temp directory'''
    temp_path = os.path.abspath(temp_folder)
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
