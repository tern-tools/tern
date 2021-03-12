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

from tern.utils import constants
from tern.utils import rootfs
from tern.classes.image_layer import ImageLayer
from tern.analyze import common as com
from tern.analyze.default import default_common as dcom
from tern.analyze.default import collect
from tern.analyze.default import bundle
from tern.analyze.default.command_lib import command_lib

# global logger
logger = logging.getLogger(constants.logger_name)


def setup():
    """For the setup, we will just need to create the working directory"""
    op_dir = rootfs.get_working_dir()
    if not os.path.isdir(op_dir):
        os.mkdir(op_dir)


def fill_packages(layer, mount_path, shell):
    """Collect package metadata and fill in the packages for the given layer
    object"""
    # For every indicator that exists on the filesystem, inventory the packages
    for bin in dcom.get_existing_bins(mount_path):
        listing = command_lib.get_base_listing(bin)
        pkg_dict, invoke_msg, warnings = collect.collect_list_metadata(
            shell, listing, work_dir=None, envs=None, mount=mount_path)
        # processing for debian copyrights
        if listing.get("pkg_format") == "deb":
            pkg_dict["pkg_licenses"] = com.get_deb_package_licenses(
                pkg_dict["copyrights"])
        if invoke_msg:
            logger.error("Script invocation error. Unable to collect some"
                         "metadata.")
        if warnings:
            logger.warning("Some metadata may be missing.")
        bundle.fill_pkg_results(layer, pkg_dict)
        com.remove_duplicate_layer_files(layer)


def execute_live(args):
    """Execute inventory at container build time
    We assume a mounted working directory is ready to inventory"""
    logger.debug('Starting analysis...')
    # create the working directory
    setup()
    # create a layer object to bundle package metadata into
    layer = ImageLayer("")
    mnt_path = os.path.abspath(args.live)
    # Find a shell that may exist in the layer
    shell = dcom.find_shell(mnt_path)
    if shell:
        # collect metadata into the layer object
        fill_packages(layer, mnt_path, shell)
        # report out the packages
    else:
        logger.critical("No shell found. Cannot run default analysis")
