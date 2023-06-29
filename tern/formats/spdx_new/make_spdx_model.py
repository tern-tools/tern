# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Common functions that are useful for all SPDX serialization formats
"""

import logging
from typing import List

from spdx_tools.spdx.model import Document, CreationInfo, Actor, ActorType, Relationship, RelationshipType

from tern.classes.image_layer import ImageLayer
from tern.classes.template import Template
from tern.formats.spdx_new.constants import DOCUMENT_ID, DOCUMENT_NAME, SPDX_VERSION, DATA_LICENSE, DOCUMENT_COMMENT, \
    LICENSE_LIST_VERSION, CREATOR_NAME, DOCUMENT_NAME_SNAPSHOT, DOCUMENT_NAMESPACE_SNAPSHOT
from tern.formats.spdx_new.file_helpers import get_layer_files_list
from tern.formats.spdx_new.general_helpers import get_current_timestamp, get_uuid
from tern.classes.image import Image
from tern.formats.spdx.spdx import SPDX
from tern.formats.spdx_new.file_helpers import get_files_list
from tern.formats.spdx_new.image_helpers import get_image_extracted_licenses, \
    get_image_dict, get_document_namespace
from tern.formats.spdx_new.layer_helpers import get_layer_dict, get_image_layer_relationships, get_layer_extracted_licenses
from tern.formats.spdx_new.package_helpers import get_packages_list, get_layer_packages_list
from tern.utils import constants

from tern.utils.general import get_git_rev_or_version

# global logger
logger = logging.getLogger(constants.logger_name)


def make_spdx_model(image_obj_list: List[Image]) -> Document:
    template = SPDX()
    # we still don't know how SPDX documents could represent multiple
    # images. Hence, we will assume only one image is analyzed and the
    # input is a list of length 1
    image_obj = image_obj_list[0]

    creation_info = CreationInfo(
        spdx_version=SPDX_VERSION,
        spdx_id=DOCUMENT_ID,
        name=DOCUMENT_NAME.format(image_name=image_obj.name),
        document_namespace=get_document_namespace(image_obj),
        creators=[Actor(actor_type=ActorType.TOOL, name=CREATOR_NAME.format(version=get_git_rev_or_version()[1]))],
        created=get_current_timestamp(),
        license_list_version=LICENSE_LIST_VERSION,
        data_license=DATA_LICENSE,
        document_comment=DOCUMENT_COMMENT,
    )
    packages = [get_image_dict(image_obj, template)]
    image_layer_relationships = get_image_layer_relationships(image_obj)

    layer_file_relationships = []
    for layer in image_obj.layers:
        package, relationships = get_layer_dict(layer)
        packages.append(package)
        layer_file_relationships.extend(relationships)

    packages.extend(get_packages_list(image_obj, template))
    files = get_files_list(image_obj, template)
    extracted_licensing_info = get_image_extracted_licenses(image_obj)

    return Document(
        creation_info=creation_info,
        packages=packages,
        files=files,
        relationships=image_layer_relationships + layer_file_relationships,
        extracted_licensing_info=extracted_licensing_info
    )


def make_spdx_model_snapshot(layer_obj: ImageLayer, template: Template) -> Document:
    """This is the SPDX document containing just the packages found at
    container build time"""
    timestamp = get_current_timestamp()

    creation_info = CreationInfo(
        spdx_version=SPDX_VERSION,
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
    packages = get_layer_packages_list(layer_obj, template)
    describes_relationships = [
        Relationship(DOCUMENT_ID, RelationshipType.DESCRIBES, package.spdx_id)
        for package in packages
    ]

    # Add list of file dictionaries, if they exist
    files = get_layer_files_list(layer_obj, template, timestamp)

    # Add package and file extracted license texts, if they exist
    extracted_licensing_info = get_layer_extracted_licenses(layer_obj)

    return Document(
        creation_info=creation_info,
        packages=packages,
        files=files,
        relationships=describes_relationships,
        extracted_licensing_info=extracted_licensing_info
    )
