# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helper functions for packages in SPDX JSON document creation
"""

from tern.report import content
from tern.formats.spdx import spdx_common


def get_package_comment(package):
    '''Given a package object, return a PackageComment string for a list of
    NoticeOrigin objects'''
    comment = ''
    if package.origins.origins:
        for notice_origin in package.origins.origins:
            comment = comment + content.print_notices(
                notice_origin, '', '\t')
    return comment


def get_package_dict(package, template):
    '''''Given a package object and its SPDX template mapping, return a SPDX
    JSON dictionary representation of the package. The analyzed files will
    go in a separate dictionary for the JSON document.'''
    mapping = package.to_dict(template)
    package_dict = {
        'name': mapping['PackageName'],
        'SPDXID': spdx_common.get_package_spdxref(package),
        'versionInfo': mapping['PackageVersion'] if mapping['PackageVersion']
        else 'NOASSERTION',
        'downloadLocation': mapping['PackageDownloadLocation'] if
        mapping['PackageDownloadLocation'] else 'NONE',
        'filesAnalyzed': 'false',  # always false for packages
        'licenseConcluded': 'NOASSERTION',  # always NOASSERTION
        'licenseDeclared': spdx_common.get_license_ref(
            mapping['PackageLicenseDeclared']) if
        mapping['PackageLicenseDeclared'] else 'NONE',
        'copyrightText': mapping['PackageCopyrightText'] if
        mapping['PackageCopyrightText'] else'NONE',
        'comment': get_package_comment(package)
    }

    return package_dict


def get_packages_list(image_obj, template):
    '''Given an image object and the template object for SPDX, return a list
    of SPDX dictionary representations for each of the packages in the image.
    The SPDX JSON spec for packages requires:
        name
        versionInfo
        downloadLocation'''
    package_dicts = []
    package_refs = set()

    for layer in image_obj.layers:
        for package in layer.packages:
            # Create a list of dictionaries. Each dictionary represents
            # one package object in the image
            pkg_ref = spdx_common.get_package_spdxref(package)
            if pkg_ref not in package_refs:
                package_dicts.append(get_package_dict(package, template))
                package_refs.add(pkg_ref)
    return package_dicts


def get_layer_packages_list(layer, template):
    """Given a layer object and a SPDX template object, return a list
    of SPDX dictionary representations for each of the packages in the layer
    and their package references"""
    package_dicts = []
    package_refs = set()
    for package in layer.packages:
        # Create a list of dictionaries. Each dictionary represents
        # one package object in the image
        pkg_ref = spdx_common.get_package_spdxref(package)
        if pkg_ref not in package_refs:
            package_dicts.append(get_package_dict(package, template))
            package_refs.add(pkg_ref)
    return package_dicts, list(package_refs)
