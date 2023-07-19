# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 VMWare, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to create an SPDX model instance from a list of Images or an ImageLayer
"""

from typing import List

from spdx_tools.spdx.model import Document, CreationInfo, Actor, ActorType, Relationship, RelationshipType, \
    PackagePurpose

from tern.classes.image_layer import ImageLayer
from tern.classes.template import Template
from tern.formats.spdx.constants import DOCUMENT_ID, DOCUMENT_NAME, DATA_LICENSE, DOCUMENT_COMMENT, \
    LICENSE_LIST_VERSION, CREATOR_NAME, DOCUMENT_NAME_SNAPSHOT, DOCUMENT_NAMESPACE_SNAPSHOT
from tern.formats.spdx.file_helpers import get_spdx_file_list_from_layer
from tern.formats.spdx.general_helpers import get_current_timestamp, get_uuid
from tern.classes.image import Image
from tern.formats.spdx.spdx_template import SPDX
from tern.formats.spdx.file_helpers import get_spdx_file_list_from_image
from tern.formats.spdx.image_helpers import get_image_extracted_licenses, \
    get_spdx_package_from_image, get_document_namespace
from tern.formats.spdx.layer_helpers import get_spdx_package_from_layer, get_image_layer_relationships, get_layer_extracted_licenses
from tern.formats.spdx.package_helpers import get_spdx_package_list_from_image, get_layer_packages_list

from tern.utils.general import get_git_rev_or_version


def make_spdx_model(image_obj_list: List[Image], spdx_version: str) -> Document:
    """Given a list of tern Images, return a complete SPDX document generated from them."""
    template = SPDX()
    # we still don't know how SPDX documents could represent multiple
    # images. Hence, we will assume only one image is analyzed and the
    # input is a list of length 1
    image_obj = image_obj_list[0]

    creation_info = CreationInfo(
        spdx_version=spdx_version,
        spdx_id=DOCUMENT_ID,
        name=DOCUMENT_NAME.format(image_name=image_obj.name),
        document_namespace=get_document_namespace(image_obj),
        creators=[Actor(actor_type=ActorType.TOOL, name=CREATOR_NAME.format(version=get_git_rev_or_version()[1]))],
        created=get_current_timestamp(),
        license_list_version=LICENSE_LIST_VERSION,
        data_license=DATA_LICENSE,
        document_comment=DOCUMENT_COMMENT,
    )
    container_package = get_spdx_package_from_image(image_obj, template, spdx_version)
    if spdx_version == "SPDX-2.3":
        container_package.primary_package_purpose = PackagePurpose.CONTAINER

    packages = [container_package]
    image_layer_relationships = get_image_layer_relationships(image_obj)

    layer_file_relationships = []
    for layer in image_obj.layers:
        package, relationships = get_spdx_package_from_layer(layer, spdx_version)
        packages.append(package)
        layer_file_relationships.extend(relationships)

    packages.extend(get_spdx_package_list_from_image(image_obj, template, spdx_version))
    files = get_spdx_file_list_from_image(image_obj, template)
    extracted_licensing_info = get_image_extracted_licenses(image_obj)

    return Document(
        creation_info=creation_info,
        packages=packages,
        files=files,
        relationships=image_layer_relationships + layer_file_relationships,
        extracted_licensing_info=extracted_licensing_info
    )


def make_spdx_model_snapshot(layer_obj: ImageLayer, template: Template, spdx_version: str) -> Document:
    """This returns the SPDX document containing just the packages found at
    container build time"""
    timestamp = get_current_timestamp()

    creation_info = CreationInfo(
        spdx_version=spdx_version,
        spdx_id=DOCUMENT_ID,
        name=DOCUMENT_NAME_SNAPSHOT,
        document_namespace=DOCUMENT_NAMESPACE_SNAPSHOT.format(timestamp=timestamp, uuid=get_uuid()),
        creators=[Actor(actor_type=ActorType.TOOL, name=CREATOR_NAME.format(get_git_rev_or_version()[1]))],
        created=timestamp,
        license_list_version=LICENSE_LIST_VERSION,
        data_license=DATA_LICENSE,
        document_comment=DOCUMENT_COMMENT,
    )

    # Add list of package dictionaries to packages list, if they exist
    packages = get_layer_packages_list(layer_obj, template, spdx_version)
    describes_relationships = [
        Relationship(DOCUMENT_ID, RelationshipType.DESCRIBES, package.spdx_id)
        for package in packages
    ]

    # Add list of file dictionaries, if they exist
    files = get_spdx_file_list_from_layer(layer_obj, template, timestamp)

    # Add package and file extracted license texts, if they exist
    extracted_licensing_info = get_layer_extracted_licenses(layer_obj)

    return Document(
        creation_info=creation_info,
        packages=packages,
        files=files,
        relationships=describes_relationships,
        extracted_licensing_info=extracted_licensing_info
    )
