# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Execution path for running tern at container image build time

The idea is that using container building primitives, a mount point on the
filesystem is already available and all that is left to do is to collect
package information.
"""
import logging
import os
from stevedore import driver
from stevedore.exception import NoMatches

from tern.utils import constants
from tern.utils import rootfs
from tern.utils import host
from tern.classes.image_layer import ImageLayer
from tern.classes.notice import Notice
from tern.analyze import common as com
from tern.analyze.default import default_common as dcom
from tern.analyze.default import core
from tern.analyze.default import collect
from tern.analyze.default import bundle
from tern.analyze.default.container import single_layer
from tern.analyze.default.command_lib import command_lib
from tern.report import report
from tern.report import formats
from tern.report import errors

# global logger
logger = logging.getLogger(constants.logger_name)


def setup():
    """For the setup, we will just need to create the working directory"""
    op_dir = rootfs.get_working_dir()
    if not os.path.isdir(op_dir):
        os.mkdir(op_dir)


def set_layer_os(layer, origin_str, binary):
    """Set layer's guessed operating system if it was not set by the
    filesystem's os-release files.
    origin_str: the string used to add notices
    binary: the listing key to look for a corresponding OS"""
    # check if the layer already has an os-release set and if not,
    # guess based on the binary
    if layer.os_guess:
        layer.origins.add_notice_to_origins(origin_str, Notice(
            formats.os_release.format(os_style=layer.os_guess), 'info'))
    else:
        layer.os_guess = command_lib.check_os_guess(binary)
        if layer.os_guess:
            layer.origins.add_notice_to_origins(origin_str, Notice(
                formats.os_style_guess.format(
                    package_manager=bin, os_list=layer.os_guess), 'info'))
        else:
            layer.origins.add_notice_to_origins(origin_str, Notice(
                errors.no_etc_release, 'warning'))


def fill_packages(layer, prereqs):
    """Collect package metadata and fill in the packages for the given layer
    object"""
    # Create an origin string to record notices
    origin_str = "Inventory Results"
    # For every indicator that exists on the filesystem, inventory the packages
    for binary in dcom.get_existing_bins(prereqs.host_path):
        set_layer_os(layer, origin_str, binary)
        prereqs.binary = binary
        listing = command_lib.get_base_listing(binary)
        pkg_dict, invoke_msg, warnings = collect.collect_list_metadata(
            listing, prereqs, True)
        # processing for debian copyrights
        if listing.get("pkg_format") == "deb":
            pkg_dict["pkg_licenses"] = com.get_deb_package_licenses(
                pkg_dict["copyrights"])
        if invoke_msg:
            logger.error("Script invocation error. Unable to collect some"
                         "metadata.")
        if warnings:
            logger.warning("Some metadata may be missing.")
        bundle.fill_pkg_results(layer, pkg_dict, listing.get("pkg_format"))
        com.remove_duplicate_layer_files(layer)


def get_context_layers(reports, format_string):
    """Given a list of reports and the format string, get corresponding layer
    objects for each of the reports. We will load the required module and
    run the consume_layer function to return the list of layers"""
    # we want to maintain consistency between the input report formats and
    # the output formats by redirecting the command line argument to the
    # correct consumer entrypoint. Hence we maintain a known pattern for
    # entrypoint strings which is simply that the corresponding consumer for
    # a given generator is the generator's entrypoint string + 'c'
    consumer_format_string = format_string + 'c'
    try:
        mgr = driver.DriverManager(
            namespace='tern.formats',
            name=consumer_format_string,
            invoke_on_load=True,
        )
        return mgr.driver.consume_layer(reports)
    except NoMatches:
        pass


def resolve_context_packages(layers):
    """We loop through the packages in the layers and remove any packages
    in the final layer that are already present in the previous layer"""
    seen = {}
    for layer in layers:
        keep_pkgs = []
        while layer.packages:
            pkg = layer.packages.pop(0)
            # we will make a string with the package name, version, and
            # checksum as a unique identifier
            pkg_str = pkg.name + pkg.version + pkg.checksum
            if pkg_str not in seen:
                # record the package string
                seen[pkg_str] = True
                keep_pkgs.append(pkg)
        for pkg in keep_pkgs:
            layer.add_package(pkg)


def execute_live(args):
    """Execute inventory at container build time
    We assume a mounted working directory is ready to inventory"""
    logger.debug('Starting analysis...')
    # create the working directory
    setup()
    # create a layer object to bundle package metadata into
    layer = ImageLayer("")
    # see if there is an os-release file at the mount point
    layer.os_guess = single_layer.find_os_release(args.live)
    # create a Prereqs object to store requirements to inventory
    prereqs = core.Prereqs()
    prereqs.host_path = os.path.abspath(args.live)
    # Find a shell that may exist in the layer
    prereqs.fs_shell = dcom.find_shell(prereqs.host_path)
    # Find the host's shell
    prereqs.host_shell = host.check_shell()
    # collect metadata into the layer object
    fill_packages(layer, prereqs)
    # resolve unique packages for this run with reports from previous runs
    if args.with_context:
        # get a list of previous layers based on plugin type
        context_layers = get_context_layers(
            args.with_context, args.report_format)
        # resolve the packages for each of the layers
        context_layers.append(layer)
        resolve_context_packages(context_layers)
        final_layer = context_layers.pop()
    else:
        final_layer = layer
    # report out the packages
    logger.debug("Preparing report")
    report.report_layer(final_layer, args)
