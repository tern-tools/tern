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
import os

from tern.analyze.passthrough import get_filesystem_command
from tern.analyze import common
from tern.classes.notice import Notice
from tern.classes.file_data import FileData
from tern.extensions.executor import Executor
from tern.utils import constants
from tern.utils import rootfs


logger = logging.getLogger(constants.logger_name)


def get_file_type(scancode_file_dict):
    '''Scancode's file dictionary has a set of keys:
        is_binary, is_text, is_archive, is_media, is_source, is_script
    using this set, return a filetype recognized by SPDX'''
    if scancode_file_dict.get('is_binary'):
        return 'BINARY'
    if scancode_file_dict.get('is_source'):
        return 'SOURCE'
    if scancode_file_dict.get('is_text'):
        return 'TEXT'
    if scancode_file_dict.get('is_archive'):
        return 'ARCHIVE'
    return 'OTHER'


def get_scancode_file(file_dict):
    '''Given a file dictionary from the scancode results, return a FileData
    object with the results'''
    # scancode records paths from the target directory onwards
    # which in tern's case is tern.utils.constants.untar_dir
    # removing that portion of the file path
    fspath = file_dict['path'].replace(
        constants.untar_dir + os.path.sep, '')
    fd = FileData(
        file_dict['name'], fspath, file_dict['date'], file_dict['file_type'])
    fd.short_file_type = get_file_type(file_dict)
    fd.add_checksums({'sha1': file_dict['sha1'], 'md5': file_dict['md5']})
    if file_dict['licenses']:
        fd.licenses = [li['short_name'] for li in file_dict['licenses']]
    fd.license_expressions = file_dict['license_expressions']
    if file_dict['copyrights']:
        fd.copyrights = [c['value'] for c in file_dict['copyrights']]
    if file_dict['urls']:
        fd.urls = [u['url'] for u in file_dict['urls']]
    fd.packages = file_dict['packages']
    fd.authors = [a['value'] for a in file_dict['authors']]
    if file_dict['scan_errors']:
        # for each scan error make a notice
        for err in file_dict['scan_errors']:
            fd.origins.add_notice_to_origins(
                'File: ' + fd.path, Notice(err, 'error'))
    return fd


def add_scancode_headers(layer_obj, headers):
    '''Given a list of headers from scancode data, add unique headers to
    the list of existing headers in the layer object'''
    unique_notices = {header.get("notice") for header in headers}
    layer_headers = layer_obj.extension_info.get("headers", list())
    for lh in layer_headers:
        unique_notices.add(lh)
    layer_obj.extension_info["headers"] = list(unique_notices)


def collect_layer_data(layer_obj):
    '''Use scancode to collect data from a layer filesystem. This function will
    create a FileData object for every file found. After scanning, it will
    return a list of FileData objects.
    '''
    files = []
    # run scancode against a directory
    command = 'scancode -ilpcu --quiet --timeout 300 --json -'
    full_cmd = get_filesystem_command(layer_obj, command)
    origin_layer = 'Layer {}'.format(layer_obj.layer_index)
    result, error = rootfs.shell_command(True, full_cmd)
    if not result:
        logger.error(
            "No scancode results for this layer: %s", str(error))
        layer_obj.origins.add_notice_to_origins(
            origin_layer, Notice(str(error), 'error'))
    else:
        # make FileData objects for each result
        data = json.loads(result)
        add_scancode_headers(layer_obj, data["headers"])
        for f in data['files']:
            if f['type'] == 'file' and f['size'] != 0:
                files.append(get_scancode_file(f))
    return files


def add_file_data(layer_obj, collected_files):
    '''Use the file data collected with scancode to fill in the file level
    data for an ImageLayer object'''
    # we'll assume that we are merging the collected_files data with
    # the file level data already in the layer object
    logger.debug("Collecting file data...")
    while collected_files:
        checkfile = collected_files.pop()
        for f in layer_obj.files:
            if f.merge(checkfile):
                break


class Scancode(Executor):
    '''Execute scancode'''
    def execute(self, image_obj, redo=False):
        '''Execution should be:
            scancode -ilpcu --quiet --json - /path/to/directory
        '''
        for layer in image_obj.layers:
            # load the layers from cache
            common.load_from_cache(layer)
            if redo or not layer.files_analyzed:
                # the layer doesn't have analyzed files, so run analysis
                file_list = collect_layer_data(layer)
                if file_list:
                    add_file_data(layer, file_list)
                    layer.files_analyzed = True
        # save data to the cache
        common.save_to_cache(image_obj)
