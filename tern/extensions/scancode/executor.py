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
from tern.classes.package import Package
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


def filter_pkg_license(declared_license):
    '''When scancode detects python package licenses, it attaches classifiers
    to the declared_license field as a dictionary object, otherwise
    it will represent the license as a string or list of strings.
    Given a scancode declared_license field, extract and return a
    license string'''
    if isinstance(declared_license, dict):
        try:
            return declared_license['license']
        except KeyError:
            # parse classifiers for PyPI licenses
            # According to https://pypi.org/pypi?%3Aaction=list_classifiers
            # we can always take the value after the last '::'
            return declared_license['classifiers'][0].split('::')[-1].strip()
    if isinstance(declared_license, list):
        for i, lic in enumerate(declared_license):
            # Some license lists from Scancode have dictionary entries
            # Extract license 'types' from license dictionaries
            if isinstance(lic, dict):
                declared_license[i] = lic["type"]
        # Get rid of duplicate licenses
        dec_lic = set(declared_license)
        return ', '.join(list(dec_lic))
    return declared_license


def get_scancode_package(package_dict):
    '''Given a package dictionary from the scancode results, return a Package
    object with the results'''
    package = Package(package_dict['name'])
    package.version = package_dict['version']
    package.pkg_license = filter_pkg_license(package_dict['declared_license'])
    package.copyright = package_dict['copyright']
    package.proj_url = package_dict['repository_homepage_url']
    package.download_url = package_dict['download_url']
    package.licenses = [package_dict['declared_license'],
                        package_dict['license_expression']]
    return package


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
    create FileData and Package objects for every File and Package found. After
    scanning, it will return a tuple with a list of FileData and a list of
    Package objects.
    '''
    files = []
    packages = []
    # run scancode against a directory
    try:
        processes = len(os.sched_getaffinity(0))
        command = "scancode -ilpcu --quiet --timeout 300 -n {} --json -".format(processes)
    except (AttributeError, NotImplementedError):
        command = "scancode -ilpcu --quiet --timeout 300 --json -"
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
                for package in f['packages']:
                    packages.append(get_scancode_package(package))
    return files, packages


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
                # file already exists and has now been updated
                break
        # file didn't previously exist in layer so add it now
        layer_obj.files.append(checkfile)


def add_package_data(layer_obj, collected_packages):
    '''Use the package data collected with scancode to fill in the package data
    for an ImageLayer object'''
    for collected_package in collected_packages:
        for package in layer_obj.packages:
            if package.merge(collected_package):
                break
        # If the package wasn't in the layer, add it
        layer_obj.packages.append(collected_package)


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
                file_list, package_list = collect_layer_data(layer)
                if file_list:
                    add_file_data(layer, file_list)
                    layer.files_analyzed = True
                add_package_data(layer, package_list)
        # save data to the cache
        common.save_to_cache(image_obj)

    def execute_layer(self, image_layer, redo=False):
        if redo or not image_layer.files_analyzed:
            file_list, package_list = collect_layer_data(image_layer)
            if file_list:
                add_file_data(image_layer, file_list)
                image_layer.files_analyzed = True
            add_package_data(image_layer, package_list)
