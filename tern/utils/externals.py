# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import logging
from enum import Enum
from packageurl import PackageURL
from urllib.parse import urlparse

from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)

class PurlType(str, Enum):
    ALPM = "alpm"
    APK = "apk"
    BITBUCKET = "bitbucket"
    CARGO = "cargo"
    COMPOSER = "composer"
    CONAN = "conan"
    CONDA = "conda"
    CRAN = "cran"
    DEB = "deb"
    DOCKER = "docker"
    GEM = "gem"
    GENERIC = "generic"
    GITHUB = "github"
    GOLANG = "golang"
    HACKAGE = "hackage"
    HEX = "hex"
    MAVEN = "maven"
    NPM = "npm"
    NUGET = "nuget"
    QPKG = "qpkg"
    OCI = "oci"
    PUB = "pub"
    PYPI = "pypi"
    RPM = "rpm"
    SWID = "swid"
    SWIFT = "swift"
    MISSING = "unknown"

def get_purl_type_from_url(proj_url):
    pkg_type = urlparse(proj_url).netloc
    if pkg_type:
        pkg_type = pkg_type.split('.')
        if len(pkg_type) > 1:
            pkg_type = pkg_type[-2]
    return pkg_type

def get_purl_type(proj_url):
    pkg_type = get_purl_type_from_url(proj_url)

    if len(pkg_type) == 0:
        return PurlType.MISSING
    if pkg_type in ('alpine', 'openwrt', 'alpinelinux'):
        return PurlType.APK
    if pkg_type == "crates":
        return PurlType.CARGO
    if pkg_type == "packagist":
        return PurlType.COMPOSER
    if pkg_type == "anaconda":
        return PurlType.CONDA
    if pkg_type == "r-project":
        return PurlType.CRAN
    if pkg_type in ('debian', 'ubuntu', 'gnu'):
        return PurlType.DEB
    if pkg_type == "rubygems":
        return PurlType.GEM
    if pkg_type == "haskell":
        return PurlType.HACKAGE
    if pkg_type == "apache":
        return PurlType.MAVEN
    if pkg_type == "npmjs":
        return PurlType.NPM
    if pkg_type == "dartlang":
        return PurlType.PUB
    if pkg_type == "python":
        return PurlType.PYPI
    return pkg_type

def get_purl_namespace():
    return ""

def generate_purl_package_reference(proj_url, pkg_name, pkg_version, qualifiers=None):
    pkg_type = get_purl_type(proj_url)
    pkg_namespace = get_purl_namespace()
    qualifiers_str = ""
    if qualifiers:
        for k,v in qualifiers.items():
            qualifiers_str += "&" + k + "=" + v
        if len(qualifiers_str) > 0:
            qualifiers_str = "?" + qualifiers_str[1:]

    return "pkg:" + pkg_type +"/" + pkg_namespace + "/" + pkg_name +  "@" + pkg_version + qualifiers_str

def add_purl(proj_url, pkg_name, pkg_version, qualifiers=None):
    purl_package_reference = generate_purl_package_reference(proj_url, pkg_name, pkg_version, qualifiers)
    purl = 'not_found'
    try:
        purl = PackageURL.from_string(purl_package_reference)
    except (ValueError):
        logger.debug("purl is missing required component for package %s",
                     purl_package_reference)
    return purl
