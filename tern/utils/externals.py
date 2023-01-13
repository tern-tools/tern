# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2022 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import logging
from packageurl import PackageURL

from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)

def generate_purl_package_reference(package_name, package_version):
    return "pkg:" + package_name +  "@" + package_version

def add_purl(package_name, package_version):
    purl_package_reference = generate_purl_package_reference(package_name, package_version)
    purl = 'not_found'
    try:
        purl = PackageURL.from_string(purl_package_reference)
    except (ValueError):
        logger.debug("purl is missing required component for package %s",
                     purl_package_reference)
    return purl
