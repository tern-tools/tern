# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Core execution - this is the special sauce of the default operation
"""

import logging

from tern.classes.notice import Notice
from tern.classes.package import Package
from tern.report import content
from tern.report import formats
from tern.report import errors
from tern.utils import constants
from tern.analyze import common as com
from tern.analyze.default.command_lib import command_lib
from tern.analyze.default import collect
from tern.analyze.default import bundle
from tern.analyze.default import default_common as dcom

# global logger
logger = logging.getLogger(constants.logger_name)


class Prereqs:
    """Set these values after instantiating an object, then pass it to the
    functions below"""
    def __init__(self):
        self.fs_shell = ''  # container filesystem shell
        self.host_shell = ''  # host shell
        self.binary = ''  # container filesystem indicator file
        self.layer_workdir = ''  # WORKDIR path
        self.host_path = ''  # layer rootfs path on host
        self.envs = None  # environment variables to set
        self.listing = None  # current listing


def execute_base(layer_obj, prereqs):
    """Given an ImageLayer object, find packages installed in the layer
    using the default method.

        1. Use command_lib's base to look up the binary to see if there
           is a method to retrieve the metadata
        2. If there is, invoke the scripts in a chroot environment and
           process the results
        3. Add the results to the ImageLayer object

    It is assumed that the filesystem is prepped for execution by mounting
    the filesystem in the working directory and /proc, /sys and /dev device
    nodes are mounted"""
    # Add notices to this layer object
    origin_layer = 'Layer {}'.format(layer_obj.layer_index)
    # find the binary listing
    listing = command_lib.get_base_listing(prereqs.binary)
    if listing:
        # put generic notice about how package metadata is collected
        snippet_msg = formats.invoke_for_base.format(binary=prereqs.binary)
        layer_obj.origins.add_notice_to_origins(
            origin_layer, Notice(snippet_msg, 'info'))
        # get list of metadata by invoking scripts in chroot
        logger.debug("Collecting metadata for image layer...")
        pkg_dict, invoke_msg, warnings = collect.collect_list_metadata(
            listing, prereqs)
        # more processing for debian copyrights to get licenses
        if listing.get("pkg_format") == "deb":
            logger.debug("Processing Debian copyrights...")
            pkg_dict["pkg_licenses"] = com.get_deb_package_licenses(
                pkg_dict["copyrights"])
        # add any errors and warnings to the layer's origins object
        if invoke_msg:
            logger.error(
                "Script invocation error. Unable to collect some metadata")
            layer_obj.origins.add_notice_to_origins(
                origin_layer, Notice(invoke_msg, 'error'))
        if warnings:
            logger.warning("Some metadata may be missing")
        # bundle the results into Package objects
        bundle.fill_pkg_results(layer_obj, pkg_dict, listing.get("pkg_format"))
        # remove extra FileData objects from the layer
        com.remove_duplicate_layer_files(layer_obj)
    # if there is no listing add a notice
    else:
        layer_obj.origins.add_notice_to_origins(
            origin_layer, Notice(errors.no_listing_for_base_key.format(
                listing_key=prereqs.binary), 'error'))


def execute_snippets(layer_obj, command_obj, prereqs):
    """Given in ImageLayer object, shell and binary to look up, find packages
    installed in the layer using the default method:
        For snippets, we will get the packages installed by the command"""
    # set up a notice origin for the layer
    origin_layer = 'Layer {}'.format(layer_obj.layer_index)
    # find packages for the command
    cmd_msg = (formats.invoke_for_snippets + '\n' +
               content.print_package_invoke(command_obj.name))
    layer_obj.origins.add_notice_to_origins(origin_layer, Notice(
        cmd_msg, 'info'))
    pkg_list = filter.get_installed_package_names(command_obj)
    # collect all the dependencies for each package name
    all_pkgs = []
    for pkg_name in pkg_list:
        pkg_invoke = command_lib.check_for_unique_package(
            prereqs.listing, pkg_name)
        deps, deps_msg = com.get_package_dependencies(
            pkg_invoke, pkg_name, prereqs.fs_shell)
        if deps_msg:
            logger.warning(deps_msg)
            layer_obj.origins.add_notice_to_origins(
                origin_layer, Notice(deps_msg, 'error'))
        all_pkgs.append(pkg_name)
        all_pkgs.extend(deps)
    unique_pkgs = list(set(all_pkgs))
    # get package metadata for each package name
    for pkg_name in unique_pkgs:
        pkg = Package(pkg_name)
        dcom.fill_package_metadata(pkg, pkg_invoke, prereqs.fs_shell,
                                   layer_obj.get_layer_workdir(), prereqs.envs)
        layer_obj.add_package(pkg)
