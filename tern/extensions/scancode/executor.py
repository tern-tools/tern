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

from tern.analyze.passthrough import get_filesystem_command
from tern.analyze.passthrough import get_file_command
from tern.classes.notice import Notice
from tern.classes.file_data import FileData
from tern.extensions.executor import Executor
from tern.utils import constants
from tern.utils import rootfs


logger = logging.getLogger(constants.logger_name)


def analyze_layer(layer_obj):
    '''Use scancode to analyze the layer's contents. Create file objects
    and add them to the layer object. Add any Notices to the FileData objects
    '''
    # run scancode against a directory
    command = 'scancode -ilpcu --quiet --json -'
    full_cmd = get_filesystem_command(layer_obj, command)
    origin_layer = 'Layer: ' + layer_obj.fs_hash[:10]
    result, error = rootfs.shell_command(True, full_cmd)
    if not result:
        logger.error(
            "No scancode results for this layer: %s", str(error))
        layer_obj.origins.add_notice_to_origins(
            origin_layer, Notice(str(error), 'error'))
    else:
        # make FileData objects for each result
        data = json.loads(result)
        for f in data['files']:
            if f['type'] == 'file':
                fd = FileData(f['name'], f['path'], f['date'], f['file_type'])
                fd.set_checksum('sha1', f['sha1'])
                if f['licenses']:
                    fd.licenses = [l['short_name'] for l in f['licenses']]
                fd.license_expressions = f['license_expressions']
                if f['copyrights']:
                    fd.copyrights = [c['value'] for c in f['copyrights']]
                if f['urls']:
                    fd.urls = [u['url'] for u in f['urls']]
                fd.packages = f['packages']
                fd.authors = f['authors']
                if f['scan_errors']:
                    # for each scan error make a notice
                    for err in f['scan_errors']:
                        fd.origins.add_notice_to_origins(
                            'File: ' + fd.path, Notice(err, 'error'))
                # add filedata object to layer
                layer_obj.add_file(fd)


def analyze_file(layer_obj):
    '''Use scancode to analyze files Tern has already found in an image layer.
    For each file in the layer, run scancode on the file. We assume that we
    already have the files names, paths and checksums filled out'''
    # run scancode against each file
    command = 'scancode -ilpcu --quiet --json -'
    for fd in layer_obj.files:
        full_cmd = get_file_command(layer_obj.tar_file, fd, command)
        origin_file = 'File: ' + fd.path
        result, error = rootfs.shell_command(True, full_cmd)
        if not result:
            logger.error(
                "No scancode results for this file: %s", str(error))
            fd.origins.add_notice_to_origins(
                origin_file, Notice(str(error), 'error'))
        else:
            # Fill the results into the FileData object
            data = json.loads(result)['files'][0]
            fd.date = data['date']
            fd.file_type = data['file_type']
            if data['licenses']:
                fd.licenses = [l['short_name'] for l in data['licenses']]
            fd.license_expressions = data['license_expressions']
            if data['copyrights']:
                fd.copyrights = [c['value'] for c in data['copyrights']]
            if data['urls']:
                fd.urls = [u['url'] for u in data['urls']]
            fd.packages = data['packages']
            fd.authors = data['authors']
            if data['scan_errors']:
                # for each scan error make a notice
                for err in data['scan_errors']:
                    fd.origins.add_notice_to_origins(
                        origin_file, Notice(err, 'error'))
            # add filedata object to layer
            layer_obj.add_file(fd)


class Scancode(Executor):
    '''Execute scancode'''
    def execute(self, image_obj):
        '''Execution should be:
            scancode -ilpcu --quiet --json - /path/to/directory
        '''
        for layer in image_obj.layers:
            layer.files_analyzed = True
            if layer.files:
                # If the layer already has files processed, then run
                # scancode per file
                analyze_file(layer)
            else:
                # If there was no file processing done, scancode will process
                # them for you
                analyze_layer(layer)
