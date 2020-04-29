# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Execute cve-bin-tool
https://github.com/intel/cve-bin-tool
This plugin does not support installation of cve-bin-tool
The assumption is that cve-bin-tool is globally executable
"""

import logging
import sys

from tern.analyze import passthrough
from tern.extensions.executor import Executor
from tern.utils import constants


logger = logging.getLogger(constants.logger_name)


class CveBinTool(Executor):
    '''Execute cve-bin-tool'''
    def execute(self, image_obj, redo=False):
        '''Execution should be:
            cve-bin-tool -u now /path/to/directory
        '''
        command = 'cve-bin-tool -u now'
        # run the command against the image filesystems
        if not passthrough.run_on_image(image_obj, command, True, redo=redo):
            logger.error("cve-bin-tool error")
            sys.exit(1)
        # for now we just print the results for each layer
        for layer in image_obj.layers:
            print(layer.analyzed_output)
