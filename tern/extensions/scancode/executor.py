# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Execute scancode
https://github.com/nexB/scancode-toolkit
This plugin does not support installation of scancode
The expected environment is as follows:
    1. Create a python3 virtual environment
    2. Clone the scancode repo here and cd into it
    3. pip install tern in this virtual environment
    4. run tern report -x scancode
"""

import json
import logging
import sys

from tern.analyze import passthrough
from tern.extensions.executor import Executor
from tern.utils import constants


logger = logging.getLogger(constants.logger_name)


class Scancode(Executor):
    '''Execute scancode'''
    def execute(self, image_obj):
        '''Execution should be:
            scancode -lpcu --quiet --json - /path/to/directory
        '''
        command = 'scancode -lpcu --quiet --json -'
        # run the command against the image filesystems
        if not passthrough.run_on_image(image_obj, command, True):
            logger.error("scancode error")
            sys.exit(1)
        # for now we just print the file path and licenses found if there are
        # any licenses are found
        for layer in image_obj.layers:
            print('Layer: {}'.format(layer.diff_id[:10]))
            results = json.loads(layer.analyzed_output)
            for afile in results['files']:
                if afile['licenses']:
                    license_str = ','.join(l['key'] for l in afile['licenses'])
                    print('{}: {}'.format(afile['path'], license_str))
