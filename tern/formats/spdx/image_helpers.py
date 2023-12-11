# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 VMWare, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Image level helpers for SPDX document generator
Images for SPDX act like a Package
"""
from typing import List

from spdx_tools.spdx.model import ExtractedLicensingInfo, Package as SpdxPackage, \
    SpdxNoAssertion

from tern.classes.image import Image
from tern.classes.template import Template
from tern.formats.spdx.layer_helpers import get_layer_licenses
from tern.formats.spdx.general_helpers import get_license_ref, get_uuid, is_valid_license_expression, \
    get_image_spdxref
from tern.utils.general import get_git_rev_or_version


def get_image_extracted_licenses(image_obj: Image) -> List[ExtractedLicensingInfo]:
    """Given an image_obj, return a unique list of ExtractedLicensingInfo
    that contains all the file and package LicenseRef and their corresponding plain text."""

    unique_licenses = set()
    for layer in image_obj.layers:
        # Get all of the unique file licenses, if they exist
        unique_licenses.update(get_layer_licenses(layer))
        # Next, collect any package licenses not already accounted for
        for package in layer.packages:
            if package.pkg_license:
                unique_licenses.add(package.pkg_license)
            # Add debian licenses from copyright text as one license
            if package.pkg_licenses:
                unique_licenses.add(", ".join(package.pkg_licenses))
    extracted_licensing_info = []
    for lic in list(unique_licenses):
        valid_spdx = is_valid_license_expression(lic)
        if not valid_spdx:
            extracted_licensing_info.append(ExtractedLicensingInfo(license_id=get_license_ref(lic), extracted_text=lic))

    return extracted_licensing_info


def get_spdx_package_from_image(image_obj: Image, template: Template, spdx_version: str) -> SpdxPackage:
    """Given an image object, the template object for SPDX and the SPDX version, return the
    SPDX Package for the given image. If the version is not SPDX-2.2, we can omit NoAssertions in most cases."""
    mapping = image_obj.to_dict(template)
    return SpdxPackage(
        spdx_id=get_image_spdxref(image_obj),
        name=mapping["PackageName"],
        download_location=SpdxNoAssertion(),
        version=mapping["PackageVersion"],
        supplier=SpdxNoAssertion(),
        files_analyzed=False,
        license_concluded=SpdxNoAssertion() if spdx_version == "SPDX-2.2" else None,
        license_declared=SpdxNoAssertion() if spdx_version == "SPDX-2.2" else None,
        copyright_text=SpdxNoAssertion() if spdx_version == "SPDX-2.2" else None,
    )


def get_document_namespace(image_obj: Image) -> str:
    """Given the image object, return a unique SPDX document uri.
    This is a combination of the tool name and version, the image name
    and the uuid"""
    return f'https://spdx.org/spdxdocs/tern-report-{get_git_rev_or_version()[1]}-{image_obj.name}-{get_uuid()}'
