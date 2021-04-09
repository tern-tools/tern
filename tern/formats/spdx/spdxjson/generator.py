# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
SPDX JSON document generator
"""

import json
import logging

from tern.formats.spdx.spdx import SPDX
from tern.formats.spdx import spdx_common
from tern.utils.general import get_git_rev_or_version
from tern.utils import constants
from tern.formats.spdx.spdxjson import formats as json_formats
from tern.formats.spdx.spdxjson import image_helpers as mhelpers
from tern.formats.spdx.spdxjson import file_helpers as fhelpers
from tern.formats.spdx.spdxjson import layer_helpers as lhelpers
from tern.formats.spdx.spdxjson import package_helpers as phelpers
from tern.formats import generator


# global logger
logger = logging.getLogger(constants.logger_name)


def get_document_namespace(image_obj):
    '''Given the image object, return a unique SPDX document uri.
    This is a combination of the tool name and version, the image name
    and the uuid'''
    return json_formats.document_namespace.format(
        version=get_git_rev_or_version()[1], image=image_obj.name,
        uuid=spdx_common.get_uuid())


def get_document_namespace_snapshot(timestamp):
    """Get the document namespace for the container image snapshot. We pass
    the timestamp so we have a common timestamp across the whole document"""
    return json_formats.document_namespace_snapshot.format(
        timestamp=timestamp, uuid=spdx_common.get_uuid())


def get_document_dict(image_obj, template):
    '''Return document info as a dictionary'''
    docu_dict = {
        'SPDXID': json_formats.spdx_id,
        'spdxVersion': json_formats.spdx_version,
        'creationInfo': {
            'created': json_formats.created.format(
                timestamp=spdx_common.get_timestamp()),
            'creators': json_formats.creator.format(
                version=get_git_rev_or_version()[1]),
            'licenseListVersion': json_formats.license_list_version,
        },
        'name': json_formats.document_name.format(image_name=image_obj.name),
        'dataLicense': json_formats.data_license,
        'comment': json_formats.document_comment,
        'documentNamespace': get_document_namespace(image_obj),
        'documentDescribes': [spdx_common.get_image_spdxref(image_obj)],
        'packages': [
            # image dict will be a single dictionary
            # we'll add the layer and package dicts later if available
            mhelpers.get_image_dict(image_obj, template)],
        'relationships': lhelpers.get_image_layer_relationships(image_obj)
    }

    # Add list of layer dictionaries to packages list
    docu_dict['packages'] += lhelpers.get_layers_list(image_obj)

    # Add list of package dictionaries to packages list, if they exist
    pkgs_dict_list = phelpers.get_packages_list(image_obj, template)
    if pkgs_dict_list:
        docu_dict['packages'] += pkgs_dict_list

    # Add list of file dictionaries, if they exist
    files = fhelpers.get_files_list(image_obj, template)
    if files:
        docu_dict['files'] = files

    # Add package and file extracted license texts, if they exist
    extracted_texts = mhelpers.get_image_extracted_licenses(image_obj)
    if extracted_texts:
        docu_dict['hasExtractedLicensingInfos'] = extracted_texts

    return docu_dict


def get_document_dict_snapshot(layer_obj, template):
    """This is the SPDX document containing just the packages found at
    container build time"""
    timestamp = spdx_common.get_timestamp()
    docu_dict = {
        'SPDXID': json_formats.spdx_id,
        'spdxVersion': json_formats.spdx_version,
        'creationInfo': {
            'created': json_formats.created.format(
                timestamp=timestamp),
            'creators': json_formats.creator.format(
                version=get_git_rev_or_version()[1]),
            'licenseListVersion': json_formats.license_list_version,
        },
        'name': json_formats.document_name_snapshot,
        'dataLicense': json_formats.data_license,
        'comment': json_formats.document_comment,
        'documentNamespace': get_document_namespace_snapshot(timestamp),
        # we will list all the unique package SPDXRefs here later
        'documentDescribes': [],
        # these will contain just the packages as there is no layer
        # package at the time of this document's generation
        'packages': [],
        # we will fill in document to package ref relationships later
        'relationships': []
    }

    # Add list of package dictionaries to packages list, if they exist
    pkgs_dict_list, package_refs = phelpers.get_layer_packages_list(
        layer_obj, template)
    if pkgs_dict_list:
        docu_dict['packages'] = pkgs_dict_list
        docu_dict['documentDescribes'] = package_refs

    # add the package relationships to the document
    for ref in package_refs:
        docu_dict['relationships'].append(json_formats.get_relationship_dict(
            json_formats.spdx_id, ref, 'DESCRIBES'))

    # Add list of file dictionaries, if they exist
    files = fhelpers.get_layer_files_list(layer_obj, template, timestamp)
    if files:
        docu_dict['files'] = files

    # Add package and file extracted license texts, if they exist
    extracted_texts = lhelpers.get_layer_extracted_licenses(layer_obj)
    if extracted_texts:
        docu_dict['hasExtractedLicensingInfos'] = extracted_texts

    return docu_dict


class SpdxJSON(generator.Generate):
    def generate(self, image_obj_list, print_inclusive=False):
        '''Generate an SPDX document
        WARNING: This assumes that the list consists of one image or the base
        image and a stub image, in which case, the information in the stub
        image is not applicable in the SPDX case as it is an empty image
        object with no metadata as nothing got built.
        The whole document should be stored in a dictionary which can be
        converted to JSON and dumped to a file using the write_report function
        in report.py.

        For the sake of SPDX, an image is a 'Package' which 'CONTAINS' each
        layer which is also a 'Package' which 'CONTAINS' the real Packages'''
        logger.debug("Generating SPDX JSON document...")

        # we still don't know how SPDX documents could represent multiple
        # images. Hence we will assume only one image is analyzed and the
        # input is a list of length 1
        image_obj = image_obj_list[0]
        template = SPDX()
        report = get_document_dict(image_obj, template)

        return json.dumps(report)

    def generate_layer(self, layer):
        """Generate an SPDX document containing package and file information
        at container build time"""
        logger.debug("Generating SPDX JSON document...")
        template = SPDX()
        report = get_document_dict_snapshot(layer, template)
        return json.dumps(report)
