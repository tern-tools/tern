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

from tern.analyze.passthrough import get_filesystem_command
from tern.classes.notice import Notice
from tern.extensions.executor import Executor
from tern.utils import constants
from tern.utils import rootfs


logger = logging.getLogger(constants.logger_name)


def run_on_image(image_obj, command):
    '''Scancode errors out when it fails to scan any file it is given even
    if it is successful with other files. Hence we cannot use the available
    run_on_image function in the passthrough module. Instead we will check
    if a json object was returned or not'''
    if not command:
        logger.error("No command to execute. No report will be generated")
        return False
    for layer in image_obj.layers:
        layer.files_analyzed = True
        full_cmd = get_filesystem_command(layer, command)
        origin_layer = 'Layer: ' + layer.fs_hash[:10]
        result, error = rootfs.shell_command(True, full_cmd)
        if not result:
            logger.error(
                "No scancode results for this layer: %s", str(error))
            layer.origins.add_notice_to_origins(
                origin_layer, Notice(str(error), 'error'))
        layer.analyzed_output = result.decode()
    return True


class Scancode(Executor):
    '''Execute scancode'''
    def execute(self, image_obj):
        '''Execution should be:
            scancode -lpcu --quiet --json - /path/to/directory
        '''
        command = 'scancode -lpcu --quiet --json -'
        # run the command against the image filesystems
        if not run_on_image(image_obj, command):
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
