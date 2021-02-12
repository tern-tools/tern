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

from tern.analyze import passthrough
from tern.extensions.executor import Executor
from tern.utils import constants


logger = logging.getLogger(constants.logger_name)


class CveBinTool(Executor):
    '''Execute cve-bin-tool'''
    def execute(self, image_obj, redo=False):
        '''Execution should be:
            cve-bin-tool -x -u now /path/to/directory
        '''
        command = 'cve-bin-tool -x -u now'
        for layer in image_obj.layers:
            # execute the command for each layer
            logger.debug("Analyzing layer %s", layer.layer_index)
            passthrough.execute_and_pass(layer, command, True)
            # for now we just print the results for each layer
            print(layer.analyzed_output)

    def execute_layer(self, image_layer, redo=False):
        command = 'cve-bin-tool -x -u now'
        logger.debug("Analyzing layer %s", image_layer.layer_index)
        passthrough.execute_and_pass(image_layer, command, True)
        # for now we just print the results for each image_layer
        print(image_layer.analyzed_output)
