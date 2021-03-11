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
import os

from tern.classes.image_layer import ImageLayer
from tern.analyze.default import common as com
from tern.analyze.default import default_common as dcom
from tern.analyze.default import collect
from tern.analyze.default import bundle
from tern.analyze.default.command_lib import command_lib


def execute_live(args):
    """Execute inventory at container build time
    We assume a mounted working directory is ready to inventory"""
    # create a layer object to bundle package metadata into
    layer = ImageLayer("")
    mnt_path = os.path.abspath(args.live)
    # Find a shell that may exist in the layer
    shell = dcom.find_shell(mnt_path)
    # For every indicator that exists on the filesystem, inventory
    # the packages
    for bin in dcom.get_existing_bins(mnt_path):
        listing = command_lib.get_base_listing(bin)
        pkg_dict, invoke_msg, warnings = collect.collect_list_metadata(
            shell, listing, args.live, work_dir=args.work_dir, envs=None)
        # processing for debian copyrights
        if listing.get("pkg_format") == "deb":
            pkg_dict["pkg_licenses"] = com.get_deb_package_licenses(
                pkg_dict["copyrights"])
        bundle.fill_pkg_results(layer, pkg_dict)
        com.remove_duplicate_layer_files(layer)
