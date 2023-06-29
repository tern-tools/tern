# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Layer level helpers for SPDX document generator
Layers for SPDX act like a Package
"""
import hashlib
import logging
import os
from typing import List, Optional, Tuple

from license_expression import Licensing

from spdx_tools.spdx.model import Package as SpdxPackage, SpdxNoAssertion, SpdxNone, PackageVerificationCode, Checksum, \
    ChecksumAlgorithm, Relationship, RelationshipType, ExtractedLicensingInfo

from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.formats.spdx_new.general_helpers import get_license_ref, is_valid_license_expression, \
    get_image_spdxref, get_package_spdxref, get_layer_spdxref, get_file_spdxref
from tern.formats.spdx_new.constants import DOCUMENT_ID
from tern.utils import constants
from tern.report import content


# global logger
logger = logging.getLogger(constants.logger_name)


def get_layer_extracted_licenses(layer_obj: ImageLayer) -> List[ExtractedLicensingInfo]:
    """Given an image_obj, return a unique list of ExtractedLicensingInfo
    that contains all the file and package LicenseRef and the corresponding plain text."""

    # Get all of the unique file licenses, if they exist
    unique_licenses = set(get_layer_licenses(layer_obj))
    # Next, collect any package licenses not already accounted for
    for package in layer_obj.packages:
        if package.pkg_license:
            unique_licenses.add(package.pkg_license)
    extracted_texts = []
    for lic in list(unique_licenses):
        valid_spdx = is_valid_license_expression(lic)
        if not valid_spdx:
            extracted_texts.append(ExtractedLicensingInfo(license_id=get_license_ref(lic), extracted_text=lic))
    return extracted_texts


def get_image_layer_relationships(image_obj: Image) -> List[Relationship]:
    """Given an image object, return a list of dictionaries describing the
    relationship between each layer "package" and the image and packages
    related to it."""
    layer_relationships = []
    image_ref = get_image_spdxref(image_obj)

    # Required - DOCUMENT_DESCRIBES relationship
    layer_relationships.append(Relationship(DOCUMENT_ID, RelationshipType.DESCRIBES, image_ref))

    for index, layer in enumerate(image_obj.layers):
        layer_ref = get_layer_spdxref(layer)
        # First, add dictionaries for the layer relationship to the image
        layer_relationships.append(Relationship(image_ref, RelationshipType.CONTAINS, layer_ref))
        # Next, add dictionary of the layer relationship to other layers
        if index != 0:
            prev_layer_ref = get_layer_spdxref(image_obj.layers[index - 1])
            layer_relationships.append(Relationship(prev_layer_ref, RelationshipType.HAS_PREREQUISITE, layer_ref))
        # Finally, add package relationships for the layer
        if layer.packages:
            for package in layer.packages:
                pkg_ref, src_ref = get_package_spdxref(package)
                layer_relationships.append(Relationship(layer_ref, RelationshipType.CONTAINS, pkg_ref))
                if src_ref:
                    layer_relationships.append(Relationship(pkg_ref, RelationshipType.GENERATED_FROM, src_ref))

    return layer_relationships


def get_layer_file_data_list(layer_obj: ImageLayer) -> List[str]:
    """Given a layer object return the SPDX list of file refs in the layer.
    Return an empty list if the files are not analyzed"""
    file_refs = []
    if layer_obj.files_analyzed:
        layer_checksum = get_layer_checksum(layer_obj)
        file_refs = [get_file_spdxref(filedata, layer_checksum.value) for filedata in layer_obj.files]
    # some files are located in different places in the filesystem
    # we make sure they don't occur as duplicates in this list
    return list(set(file_refs))


def get_layer_package_comment(layer_obj: ImageLayer) -> str:
    """Return a package comment string value for a list of NoticeOrigin
    objects for the given layer object"""
    comment = ''
    if "headers" in layer_obj.extension_info.keys():
        for header in layer_obj.extension_info.get("headers"):
            comment += header
            comment += '\n'
    if not layer_obj.origins.is_empty():
        for notice_origin in layer_obj.origins.origins:
            comment += content.print_notices(notice_origin, '', '\t')
    return comment


def get_layer_dict(layer_obj: ImageLayer) -> Tuple[SpdxPackage, List[Relationship]]:
    """Given a layer object, return an SPDX Package representation
     of the layer and the list of CONTAINS relationships to all files in that layer.
     The analyzed files will go in a separate part of the document."""

    comment = get_layer_package_comment(layer_obj)
    verification_code = get_layer_verification_code(layer_obj) if layer_obj.files_analyzed else None

    layer_licenses = get_layer_licenses(layer_obj)
    license_info_from_files = []
    if layer_licenses:
        # Use the layer LicenseRef in the list instead of license expression
        for lic in layer_licenses:
            license_info_from_files.append(get_license_ref(lic))  # TODO: potential bug here that converts valid expressions to LicenseRef- identifiers
    license_info_from_files = [Licensing().parse(lic) for lic in license_info_from_files]

    layer_spdx_id = get_layer_spdxref(layer_obj)
    package = SpdxPackage(
        spdx_id=layer_spdx_id,
        name=os.path.basename(layer_obj.tar_file),
        version=layer_obj.layer_index,
        supplier=SpdxNoAssertion(),
        file_name=layer_obj.tar_file,
        download_location=SpdxNone(),
        files_analyzed=bool(layer_obj.files_analyzed),
        verification_code=verification_code,
        checksums=[get_layer_checksum(layer_obj)],
        license_concluded=SpdxNoAssertion(),
        license_declared=SpdxNoAssertion(),
        copyright_text=SpdxNoAssertion(),
        comment=comment if comment else None,
        license_info_from_files=license_info_from_files,
    )

    relationships = [
        Relationship(layer_spdx_id, RelationshipType.CONTAINS, file_ref)
        for file_ref in get_layer_file_data_list(layer_obj)
    ]

    return package, relationships


def get_layer_licenses(layer_obj: ImageLayer) -> List[str]:
    """Return a list of unique licenses from the files analyzed
    in the layer object. It is assumed that the files were analyzed and
    there should be some license expressions. If there are not, an empty list
    is returned"""
    licenses = set()
    for filedata in layer_obj.files:
        # we will use the SPDX license expressions here as they will be
        # valid SPDX license identifiers
        if filedata.licenses:
            for lic in list(set(filedata.licenses)):
                licenses.add(lic)
    return list(licenses)


def get_layer_verification_code(layer_obj: ImageLayer) -> Optional[PackageVerificationCode]:
    """Calculate the verification code from the files in an image layer. This
    assumes that layer_obj.files_analyzed is True. The implementation follows
    the algorithm in the SPDX spec v 2.2 which requires SHA1 to be used to
    calculate the checksums of the file and the final verification code"""
    sha1_list = []
    for filedata in layer_obj.files:
        filesha = filedata.get_checksum('sha1')
        if not filesha:
            # we cannot create a verification code, hence file generation
            # is aborted
            logger.critical(
                'File %s does not have a sha1 checksum. Failed to generate '
                'an SPDX report', filedata.path)
            return None
        sha1_list.append(filesha)
    sha1_list.sort()
    sha1s = ''.join(sha1_list)
    verification_code = hashlib.sha1(sha1s.encode('utf-8')).hexdigest()  # nosec
    return PackageVerificationCode(verification_code)


def get_layer_checksum(layer_obj: ImageLayer) -> Checksum:
    return Checksum(
        ChecksumAlgorithm[layer_obj.checksum_type.upper()],
        layer_obj.checksum
    )
