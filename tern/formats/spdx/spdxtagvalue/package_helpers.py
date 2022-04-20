# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Helper functions for packages in SPDX document
"""

from license_expression import get_spdx_licensing
from tern.formats.spdx.spdxtagvalue import formats as spdx_formats
from tern.formats.spdx import spdx_common
from tern.report import content


def is_spdx_license_expression(license_data):
    '''Return True if the license is a valid SPDX license expression, else
    return False'''
    licensing = get_spdx_licensing()
    if ',' in license_data:
        license_data = license_data.replace(',', ' ')
    return licensing.validate(license_data).errors == []

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


def get_package_license_declared(package_license_declared):
    if package_license_declared:
        if is_spdx_license_expression(package_license_declared):
            return package_license_declared
        return spdx_common.get_license_ref(package_license_declared)
    return 'NONE'


def get_source_package_block(package_obj, template):
    '''Given a package object and its SPDX template mapping, return a SPDX
    document block for the corresponding source package.
    The mapping should have keys:
        SourcePackageName
        SourcePackageVersion
        PackageLicenseDeclared
        PackageCopyrightText
        PackageDownloadLocation'''
    block = ''
    mapping = package_obj.to_dict(template)
    # Source Package Name
    block += 'PackageName: {}\n'.format(mapping['SourcePackageName'])
    # Source SPDXID
    _, spdx_ref_src = spdx_common.get_package_spdxref(package_obj)
    block += 'SPDXID: {}\n'.format(spdx_ref_src)
    # Source Package Version
    if mapping['SourcePackageVersion']:
        block += 'PackageVersion: {}\n'.format(
            mapping['SourcePackageVersion'])
    # Package Download Location (Same as binary)
    if mapping['PackageDownloadLocation']:
        block += 'PackageDownloadLoaction: {}\n'.format(
            mapping['PackageDownloadLocation'])
    else:
        block += 'PackageDownloadLocation: NOASSERTION\n'
    # Files Analyzed (always false for packages)
    block += 'FilesAnalyzed: false\n'
    # Package License Concluded (always NOASSERTION)
    block += 'PackageLicenseConcluded: NOASSERTION\n'
    # Package License Declared (use the license ref for this)
    block += 'PackageLicenseDeclared: ' + get_package_license_declared(
        mapping['PackageLicenseDeclared']) + '\n'
    # Package Copyright Text
    if mapping['PackageCopyrightText']:
        block += 'PackageCopyrightText:' + spdx_formats.block_text.format(
            message=mapping['PackageCopyrightText']) + '\n'
    else:
        block += 'PackageCopyrightText: NONE\n'
    # Package Comments
    block += spdx_formats.source_comment
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
    spdx_ref, _ = spdx_common.get_package_spdxref(package_obj)
    block += 'SPDXID: {}\n'.format(spdx_ref)
    # Package Version
    if mapping['PackageVersion']:
        block += 'PackageVersion: {}\n'.format(mapping['PackageVersion'])
    # Package Download Location
    if mapping['PackageDownloadLocation']:
        block += 'PackageDownloadLoaction: {}\n'.format(
            mapping['PackageDownloadLocation'])
    else:
        block += 'PackageDownloadLocation: NOASSERTION\n'
    # Files Analyzed (always false for packages)
    block += 'FilesAnalyzed: false\n'
    # Package License Concluded (always NOASSERTION)
    block += 'PackageLicenseConcluded: NOASSERTION\n'
    # Package License Declared (use the license ref for this)
    block += 'PackageLicenseDeclared: ' + get_package_license_declared(
        mapping['PackageLicenseDeclared']) + '\n'
    # Package Copyright Text
    if mapping['PackageCopyrightText']:
        block += 'PackageCopyrightText:' + spdx_formats.block_text.format(
            message=mapping['PackageCopyrightText']) + '\n'
    else:
        block += 'PackageCopyrightText: NONE\n'
    # Package Comments
    block += get_package_comment(package_obj)
    return block
