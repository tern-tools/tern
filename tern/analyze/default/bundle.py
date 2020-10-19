# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to bundle results into an image object
"""

from tern.classes.notice import Notice
from tern.command_lib import command_lib
from tern.report import formats
from tern.report import errors


def add_base_packages(image_layer, binary, shell, work_dir=None, envs=None):
    '''Given the image layer, the binary to invoke and shell:
        1. get the listing from the base.yml
        2. Invoke any commands against the base layer
        3. Make a list of packages and add them to the layer'''
    origin_layer = 'Layer {}'.format(image_layer.layer_index)
    if image_layer.created_by:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.layer_created_by.format(created_by=image_layer.created_by),
            'info'))
    else:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.no_created_by, 'warning'))
    origin_command_lib = formats.invoking_base_commands
    # find the binary
    listing = command_lib.get_base_listing(binary)
    if listing:
        # put info notice about what is going to be invoked
        snippet_msg = (formats.invoke_for_base + '\n' +
                       content.print_base_invoke(binary))
        image_layer.origins.add_notice_to_origins(
            origin_layer, Notice(snippet_msg, 'info'))
        # get all the packages in the base layer
        pkg_dict, invoke_msg, warnings = collate_list_metadata(shell, listing,
                                                               work_dir, envs)

        if listing.get("pkg_format") == "deb":
            pkg_dict["pkg_licenses"] = get_deb_package_licenses(
                pkg_dict["copyrights"])

        if invoke_msg:
            image_layer.origins.add_notice_to_origins(
                origin_layer, Notice(invoke_msg, 'error'))
        if warnings:
            image_layer.origins.add_notice_to_origins(
                origin_command_lib, Notice(warnings, 'warning'))
        if 'names' in pkg_dict and len(pkg_dict['names']) > 1:
            pkg_list = convert_to_pkg_dicts(pkg_dict)
            for pkg_dict in pkg_list:
                pkg = Package(pkg_dict['name'])
                pkg.fill(pkg_dict)
                image_layer.add_package(pkg)
            remove_duplicate_layer_files(image_layer)
    # if there is no listing add a notice
    else:
        image_layer.origins.add_notice_to_origins(
            origin_command_lib, Notice(errors.no_listing_for_base_key.format(
                listing_key=binary), 'error'))
