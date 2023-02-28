# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helper functions for packages in SPDX JSON document creation
"""

from tern.report import content
from tern.formats.spdx import spdx_common
from tern.formats.spdx.spdxjson import formats as json_formats


def get_package_comment(package):
    '''Given a package object, return a PackageComment string for a list of
    NoticeOrigin objects'''
    comment = ''
    if package.origins.origins:
        for notice_origin in package.origins.origins:
            comment = comment + content.print_notices(
                notice_origin, '', '\t')
    return comment


def get_source_package_dict(package, template):
    '''''Given a package object and its SPDX template mapping, return a SPDX
    JSON dictionary representation of the associated source package.
    The analyzed files will go in a separate dictionary for the
    JSON document.'''
    mapping = package.to_dict(template)
    _, src_ref = spdx_common.get_package_spdxref(package)
    declared_lic = mapping['PackageLicenseDeclared']
    # Define debian licenses from copyright text as one license 
    if package.pkg_format == 'deb':
        declared_lic = ', '.join(package.pkg_licenses)
    package_dict = {
        'name': mapping['SourcePackageName'],
        'SPDXID': src_ref,
        'versionInfo': mapping['SourcePackageVersion'] if
        mapping['SourcePackageVersion'] else 'NOASSERTION',
        'downloadLocation': mapping['PackageDownloadLocation'] if
        mapping['PackageDownloadLocation'] else 'NOASSERTION',
        'filesAnalyzed': False,  # always false for packages
        'licenseConcluded': 'NOASSERTION',  # always NOASSERTION
        'licenseDeclared': spdx_common.get_package_license_declared(
            declared_lic),
        'copyrightText': mapping['PackageCopyrightText'] if
        mapping['PackageCopyrightText'] else 'NONE',
        'comment': json_formats.source_package_comment
    }

    return package_dict


def get_package_dict(package, template):
    '''''Given a package object and its SPDX template mapping, return a SPDX
    JSON dictionary representation of the package. The analyzed files will
    go in a separate dictionary for the JSON document.'''
    mapping = package.to_dict(template)
    supplier_str = 'Organization: ' + mapping['PackageSupplier']
    pkg_ref, _ = spdx_common.get_package_spdxref(package)
    package_dict = {
        'name': mapping['PackageName'],
        'SPDXID': pkg_ref,
        'versionInfo': mapping['PackageVersion'] if mapping['PackageVersion']
        else 'NOASSERTION',
        'supplier': supplier_str if mapping['PackageSupplier'] else 'NOASSERTION', 
        'downloadLocation': mapping['PackageDownloadLocation'] if
        mapping['PackageDownloadLocation'] else 'NOASSERTION',
        'filesAnalyzed': False,  # always false for packages
        'licenseConcluded': 'NOASSERTION',  # always NOASSERTION
        'licenseDeclared':  spdx_common.get_package_license_declared(
            mapping['PackageLicenseDeclared']),
        'copyrightText': mapping['PackageCopyrightText'] if
        mapping['PackageCopyrightText'] else 'NONE',
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
            pkg_ref, src_ref = spdx_common.get_package_spdxref(package)
            if pkg_ref not in package_refs and package.name:
                package_dicts.append(get_package_dict(package, template))
                package_refs.add(pkg_ref)
            if src_ref and src_ref not in package_refs:
                package_dicts.append(get_source_package_dict(
                    package, template))
                package_refs.add(src_ref)
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
