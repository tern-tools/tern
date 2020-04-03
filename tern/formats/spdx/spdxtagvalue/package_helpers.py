# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helper functions for packages in SPDX document
"""

import hashlib

from tern.formats.spdx import formats as spdx_formats
from tern.report import content


def get_package_spdxref(package_obj):
    '''Given the package object, return an SPDX reference ID'''
    return 'SPDXRef-{}'.format(
        spdx_formats.package_id.format(
            name=package_obj.name,
            ver=package_obj.version).replace(':', '-', 1))


def get_package_comment(package_obj):
    '''Return a PackageComment tag-value text block for a list of
    NoticeOrigin objects'''
    comment = ''
    if package_obj.origins.origins:
        for notice_origin in package_obj.origins.origins:
            comment = comment + content.print_notices(
                notice_origin, '', '\t')
        return spdx_formats.package_comment.format(comment=comment)
    return comment


def get_package_license_ref(package_license):
    '''Return a LicenseRef with a unique SHA-256 ID for the package object
    if it exists.'''
    return 'LicenseRef-' + hashlib.sha256(package_license.encode(
        'utf-8')).hexdigest()[-7:]


def get_unique_license_list(pkg_obj_list):
    '''Given a list of package objects, return a list of unique license
    texts. Don't include empty licenses'''
    licenses = set()
    for pkg in pkg_obj_list:
        if pkg.pkg_license:
            licenses.add(pkg.license)
    return list(licenses)


def get_package_license_block(pkg_obj_list):
    '''Given a list of package objects, return a LicenseRef block of text
    this is of the format:
        ## License Information
        LicenseID: LicenseRef-MIT
        ExtractedText: <text> </text>'''
    block = ''
    license_list = get_unique_license_list(pkg_obj_list)
    for l in license_list:
        block = block + spdx_formats.license_id.format(
            license_ref=get_package_license_ref(l)) + '\n'
        block = block + spdx_formats.extracted_text.format(
            orig_license=l) + '\n\n'
    return block


def get_package_block(package_obj, template):
    '''Given a package object and its SPDX template mapping, return a SPDX
    document block for the package. The mapping should have keys:
        PackageName
        PackageVersion
        PackageLicenseDeclared
        PackageCopyrightText
        PackageDownloadLocation'''
    block = ''
    mapping = package_obj.to_dict(template)
    # Package Name
    block += 'PackageName: {}\n'.format(mapping['PackageName'])
    # SPDXID
    block += 'SPDXID: {}\n'.format(get_package_spdxref(package_obj))
    # Package Version
    if mapping['PackageVersion']:
        block += 'PackageVersion: {}\n'.format(mapping['PackageVersion'])
    # Package Download Location
    if mapping['PackageDownloadLocation']:
        block += 'PackageDownloadLoaction: {}\n'.format(
            mapping['PackageDownloadLocation'])
    else:
        block += 'PackageDownloadLocation: NONE\n'
    # Files Analyzed (always false for packages)
    block += 'FilesAnalyzed: false\n'
    # Package License Concluded (always NOASSERTION)
    block += 'PackageLicenseConcluded: NOASSERTION\n'
    # Package License Declared (use the license ref for this)
    if mapping['PackageLicenseDeclared']:
        block += 'PackageLicenseDeclared: {}\n'.format(
            get_package_license_ref(mapping['PackageLicenseDeclared']))
    else:
        block += 'PackageLicenseDeclared: NONE\n'
    # Package Copyright Text
    if mapping['PackageCopyrightText']:
        block += 'PackageCopyrightText:' + spdx_formats.block_text.format(
            mapping['PackageCopyrightText']) + '\n'
    else:
        block += 'PackageCopyrightText: NONE\n'
    # Package Comments
    block += get_package_comment(package_obj)
    return block
