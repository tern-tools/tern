# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Patrick Dwyer. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

'''
CycloneDX JSON document generator
'''

import json
import logging

from tern.utils import constants
from tern.formats import generator
from tern.formats.cyclonedx import cyclonedx_common
from tern.formats.cyclonedx.cyclonedxjson import image_helpers as mhelpers
from tern.formats.cyclonedx.cyclonedxjson import package_helpers as phelpers


# global logger
logger = logging.getLogger(constants.logger_name)


def get_document_dict(image_obj_list):
    ''' Return document info as a dictionary '''
    docu_dict = {
        'bomFormat': 'CycloneDX',
        'specVersion': '1.3',
        'serialNumber': cyclonedx_common.get_serial_number(),
        'version': 1,
        'metadata': {
            'timestamp': cyclonedx_common.get_timestamp(),
            'tools': [cyclonedx_common.metadata_tool],
        },
        'components': [],
    }

    # if representing a single image populate top level BOM metadata component
    # else representing multiple images so list them as components
    if len(image_obj_list) == 1:
        docu_dict['metadata']['component'] = mhelpers.get_image_dict(image_obj_list[0])
        docu_dict['components'] = phelpers.get_packages_list(image_obj_list[0])
    else:
        for image_obj in image_obj_list:
            image_componet = mhelpers.get_image_dict(image_obj)
            image_componet['components'] = phelpers.get_packages_list(image_obj)
            docu_dict['components'].append(image_componet)

    return docu_dict


class CycloneDXJSON(generator.Generate):
    def generate(self, image_obj_list, print_inclusive=False):
        ''' Generate a CycloneDX document
        The whole document should be stored in a dictionary which can be
        converted to JSON and dumped to a file using the write_report function
        in report.py. '''
        logger.debug('Generating CycloneDX JSON document...')

        report = get_document_dict(image_obj_list)

        return json.dumps(report, indent=2)
