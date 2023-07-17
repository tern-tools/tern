# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 VMWare, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Package level helpers for SPDX document generator
"""
from typing import List

from packageurl import PackageURL
from spdx_tools.spdx.model import Package as SpdxPackage, SpdxNoAssertion, SpdxNone, Actor, ActorType, \
    ExternalPackageRef, ExternalPackageRefCategory

from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.classes.package import Package
from tern.classes.template import Template
from tern.formats.spdx_new.general_helpers import get_package_license_declared, get_package_spdxref
from tern.report import content


SOURCE_PACKAGE_COMMENT = 'This package refers to a source package associated' \
    ' with one or more binary packages installed in this container. ' \
    'This source pacakge is NOT installed in the container but may be useful' \
    ' for CVE lookups.'


def get_layer_packages_list(layer: ImageLayer, template: Template) -> List[SpdxPackage]:
    """Given a layer object and an SPDX template object, return a list
    of SPDX dictionary representations for each of the packages in the layer
    and their package references"""
    package_dicts = []
    package_refs = []
    for package in layer.packages:
        # Create a list of SpdxPackages, each one representing
        # one package object in the image
        pkg_ref = get_package_spdxref(package)
        if pkg_ref not in package_refs:
            package_dicts.append(get_package_dict(package, template))
            package_refs.append(pkg_ref)
    return package_dicts


def get_package_comment(package: Package) -> str:
    """Given a package object, return a PackageComment string for a list of
    NoticeOrigin objects"""
    comment = ''
    if package.origins.origins:
        for notice_origin in package.origins.origins:
            comment = comment + content.print_notices(
                notice_origin, '', '\t')
    return comment


def get_source_package_dict(package: Package, template: Template) -> SpdxPackage:
    """Given a package object and its SPDX template mapping, return an SPDX Package of the associated source package.
    The analyzed files will go in a separate dictionary for the JSON document."""
    mapping = package.to_dict(template)

    _, src_ref = get_package_spdxref(package)
    declared_lic = mapping['PackageLicenseDeclared']
    # Define debian licenses from copyright text as one license
    if package.pkg_format == 'deb':
        declared_lic = ', '.join(package.pkg_licenses)

    return SpdxPackage(
        spdx_id=src_ref,
        name=mapping['SourcePackageName'],
        version=mapping['SourcePackageVersion'] if mapping['SourcePackageVersion'] else 'NOASSERTION',
        download_location=mapping['PackageDownloadLocation'] if mapping['PackageDownloadLocation'] else SpdxNoAssertion(),
        files_analyzed=False,
        license_concluded=SpdxNoAssertion(),
        license_declared=get_package_license_declared(declared_lic),
        copyright_text=mapping['PackageCopyrightText'] if mapping['PackageCopyrightText'] else SpdxNone(),
        comment=SOURCE_PACKAGE_COMMENT,
    )


def get_package_dict(package: Package, template: Template) -> SpdxPackage:
    """Given a package object and its SPDX template mapping, return an SPDX Package.
    The analyzed files will go in a separate dictionary for the JSON document."""
    mapping = package.to_dict(template)

    if mapping['PackageSupplier']:
        supplier = Actor(ActorType.ORGANIZATION, mapping['PackageSupplier'])
    else:
        supplier = SpdxNoAssertion()

    external_ref = []
    if get_purl(package):
        external_ref.append(ExternalPackageRef(
            ExternalPackageRefCategory.PACKAGE_MANAGER,
            "purl",
            get_purl(package)
        ))

    pkg_ref, _ = get_package_spdxref(package)
    # Define debian licenses from copyright text as one license
    declared_lic = mapping['PackageLicenseDeclared']
    if package.pkg_format == 'deb':
        declared_lic = ', '.join(package.pkg_licenses)

    return SpdxPackage(
        spdx_id=pkg_ref,
        name=mapping['PackageName'],
        version=mapping['PackageVersion'] if mapping['PackageVersion'] else 'NOASSERTION',
        supplier=supplier,
        download_location=mapping['PackageDownloadLocation'] if mapping['PackageDownloadLocation'] else SpdxNoAssertion(),
        files_analyzed=False,
        license_concluded=SpdxNoAssertion(),
        license_declared=get_package_license_declared(declared_lic),
        copyright_text=mapping['PackageCopyrightText'] if mapping['PackageCopyrightText'] else SpdxNone(),
        external_references=external_ref,
        comment=get_package_comment(package),
    )


def get_packages_list(image_obj: Image, template: Template) -> List[SpdxPackage]:
    """Given an image object and the template object for SPDX, return a list
    of SPDX dictionary representations for each of the packages in the image.
    The SPDX JSON spec for packages requires:
        name
        versionInfo
        downloadLocation"""
    packages = []
    package_refs = set()

    for layer in image_obj.layers:
        for package in layer.packages:
            # Create a list of dictionaries. Each dictionary represents
            # one package object in the image
            pkg_ref, src_ref = get_package_spdxref(package)
            if pkg_ref not in package_refs and package.name:
                packages.append(get_package_dict(package, template))
                package_refs.add(pkg_ref)
            if src_ref and src_ref not in package_refs:
                packages.append(get_source_package_dict(
                    package, template))
                package_refs.add(src_ref)
    return packages


purl_types_with_namespaces = [
    'deb',
    'rpm',
    'apk',
    'alpm'
]


def get_purl(package_obj: Package) -> str:
    """Return a purl string for a given package"""
    purl_type = package_obj.pkg_format
    purl_namespace = ''
    if purl_type in purl_types_with_namespaces and package_obj.pkg_supplier:
        # https://github.com/package-url/purl-spec/pull/214
        if package_obj.pkg_supplier.split(' ')[0] == "VMware":
            purl_namespace = package_obj.pkg_supplier.split(' ')[1].lower()
        else:
            purl_namespace = package_obj.pkg_supplier.split(' ')[0].lower()
            # TODO- this might need adjusting for alpm. Currently can't test on M1
    purl = PackageURL(purl_type, purl_namespace, package_obj.name.lower(), package_obj.version,
                      qualifiers={'arch': package_obj.arch if package_obj.arch else ''})
    try:
        return purl.to_string()
    except ValueError:
        return ''
