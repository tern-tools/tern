# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
SPDX document generator
"""

import datetime

from tern.formats.spdx.spdx import SPDX
from tern.utils.general import get_git_rev_or_version
from tern.report import content
from tern.formats.spdx import formats as spdx_formats
from tern.formats import generator


def get_document_namespace(image_obj):
    '''Given the image object, return a unique SPDX document uri.
    This is a combination of the human readable id from the image
    object and the tool name'''
    return spdx_formats.document_namespace.format(
        image_id=image_obj.get_human_readable_id(),
        version=get_git_rev_or_version()[1])


def get_package_spdxref(package_obj):
    '''Given the package object, return an SPDX reference ID'''
    return 'SPDXRef-{}'.format(package_obj.get_package_id())


def get_layer_spdxref(layer_obj):
    '''Given the layer object, return an SPDX reference ID'''
    # here we return the shortened diff_id of the layer
    return 'SPDXRef-{}'.format(layer_obj.diff_id[:10])


def get_image_spdxref(image_obj):
    '''Given the image object, return an SPDX reference ID'''
    # here we return the image name, tag and id
    return 'SPDXRef-{}'.format(image_obj.get_human_readable_id())


def get_document_block(image_obj):
    '''Return document related SPDX tag-values'''
    block = spdx_formats.spdx_version + '\n'
    block = block + spdx_formats.data_license + '\n'
    block = block + spdx_formats.spdx_id + '\n'
    block = block + spdx_formats.document_name.format(
        image_name=image_obj.get_human_readable_id()) + '\n'
    block = block + get_document_namespace(image_obj) + '\n'
    block = block + spdx_formats.license_list_version + '\n'
    block = block + spdx_formats.creator.format(
        version=get_git_rev_or_version()[1]) + '\n'
    block = block + spdx_formats.created.format(
        timestamp=datetime.datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%SZ")) + '\n'
    block = block + spdx_formats.document_comment + '\n'
    return block


def get_package_comment(origins):
    '''Return a PackageComment tag-value text block for a list of
    NoticeOrigin objects'''
    comment = ''
    if origins:
        for notice_origin in origins:
            comment = comment + content.print_notices(
                notice_origin, '', '\t')
        return spdx_formats.package_comment.format(comment=comment)
    return comment


def get_main_block(level_dict, origins, **kwargs):
    '''Given the dictionary for the level, the list of notices and a list of
    key-value pairs, return the SPDX tag-value information for this level'''
    block = ''
    for key, value in level_dict.items():
        block = block + spdx_formats.tag_value.format(
            tag=key, value=value if value else 'NOASSERTION') + '\n'
    # list specifically defined tag-values
    for key, value in kwargs.items():
        block = block + spdx_formats.tag_value.format(
            tag=key, value=value) + '\n'
    block = block + get_package_comment(origins) + '\n'
    return block


def get_image_relationships(image_obj):
    '''Given the image object, return the relationships to the layers'''
    block = ''
    image_reference = get_image_spdxref(image_obj)
    for layer in image_obj.layers:
        block = block + spdx_formats.contains.format(
            outer=image_reference, inner=get_layer_spdxref(layer)) + '\n'
    return block


def get_layer_relationships(layer_obj, prev_layer_spdxref=None):
    '''Given the layer object, return the relationships of the layer
    objects to packages and to the previous layer'''
    block = ''
    layer_reference = get_layer_spdxref(layer_obj)
    if prev_layer_spdxref:
        block = block + spdx_formats.prereq.format(
            after=layer_reference, before=prev_layer_spdxref) + '\n'
    for package in layer_obj.packages:
        block = block + spdx_formats.contains.format(
            outer=layer_reference, inner=get_package_spdxref(package)) + '\n'
    return block


def get_license_ref(pkg_license):
    '''Given one license, return a LicenseRef'''
    return 'LicenseRef-' + pkg_license


def get_package_licenses(license_string):
    '''Return a list of strings from the original license in the Package
    object. This takes in the string'''
    return license_string.split(' ')


def update_license_list(license_list, license_string):
    '''SPDX has a LicenseRef block at the end of the document that has
    all the license references in the document. To make this work,
    take in a list containing all the licenses seen thus far, and a license
    string from the package manager. If the individual license in the license
    string is not in the list, add it'''
    licenses = get_package_licenses(license_string)
    for l in licenses:
        if l not in license_list:
            license_list.append(l)


def format_license(license_string):
    '''Given a license string, return an SPDX formatted license string.
    NOTE: this is a quickfix
    We will split up the licenses by spaces, prepend each string with a
    "LicenseRef-" and then join the strings with an " AND "'''
    license_list = get_package_licenses(license_string)
    amended_license_list = [get_license_ref(l) for l in license_list]
    return ' AND '.join(amended_license_list)


def get_license_block(license_list):
    '''Given a list of individual licenses, return a LicenseRef block of text
    this is of the format:
        ## License Information
        LicenseID: LicenseRef-MIT
        ExtractedText: <text> </text>'''
    # make a list of individual licenses
    block = ''
    for l in license_list:
        block = block + spdx_formats.license_id.format(
            license_ref=get_license_ref(l)) + '\n'
        block = block + spdx_formats.extracted_text.format(
            orig_license=l) + '\n\n'
    return block


class SpdxTagValue(generator.Generate):
    def generate(self, image_obj_list):
        '''Generate an SPDX document
        WARNING: This assumes that the list consists of one image or the base
        image and a stub image, in which case, the information in the stub
        image is not applicable in the SPDX case as it is an empty image
        object with no metadata as nothing got built.
        The whole document should be stored in a string which can be written
        to a file using the write_report function in report.py
        First convert the image object into a dictionary. The dictionary
        should be in this form:
            image:{
              origins: [...]
              layers: [
                {origins: [...],
                 packages: [
                   {origins: [...], package1: {...}},
                   {origins: [...], package2: {...}}...]}, ...]}
        Then convert this into a flat format starting from top to bottom
        So:
            ## image
            List all the tag-values here
            make a PackageComment: <text> </text>

            ## relationships
            spdx-ref CONTAINS layer1
            spdx-ref CONTAINS layer2
            ...

            ## layer1
            List all the tag-values here
            make a PackageComment here

            # relationships
            spdx-ref CONTAINS package1
            spdx-ref CONTAINS package2
            ....

            # layer2
            tag-values
            PackageComment

            # relationships
            spdx-ref HAS_PREREQUISITE layer1
            spdx-ref CONTAINS package3
            spdx-ref CONTAINS package4

            ....

            # package1
            tag-values
            PackageComment

            # package2

            # package3

            # package4


        Everything in Origins can be in a tag-value format as
        PackageComment: <text> </text>

        For the sake of SPDX, an image is a 'Package' which 'CONTAINS' each
        layer which is also a 'Package' which 'CONTAINS' the real Package'''
        report = ''
        licenses_found = []  # This is needed for unrecognized license strings
        image_obj = image_obj_list[0]
        template = SPDX()
        # The image's PackageDownloadLocation is from a container registry
        # This includes all the layers but the packages' download location
        # is unknown if the download_url is blank
        registry_repotag = image_obj.get_download_location() if hasattr(
            image_obj, 'repotag') else 'NOASSERTION'

        # first part is the document tag-value
        # this doesn't change at all
        report = report + get_document_block(image_obj) + '\n'

        # this part is the image part and needs
        # the image object
        report = report + get_main_block(
            image_obj.to_dict(template),
            image_obj.origins.origins,
            SPDXID=get_image_spdxref(image_obj),
            PackageLicenseDeclared='NOASSERTION',
            PackageLicenseConcluded='NOASSERTION',
            PackageCopyrightText='NOASSERTION',
            FilesAnalyzed='false') + '\n'
        # Add image relationships
        report = report + get_image_relationships(image_obj) + '\n'

        # Add the layer part for each layer
        for index, layer_obj in enumerate(image_obj.layers):
            # this is the main block for the layer
            report = report + get_main_block(
                layer_obj.to_dict(template),
                layer_obj.origins.origins,
                SPDXID=get_layer_spdxref(layer_obj),
                PackageDownloadLocation=registry_repotag,
                PackageLicenseDeclared='NOASSERTION',
                PackageLicenseConcluded='NOASSERTION',
                PackageCopyrightText='NOASSERTION',
                FilesAnalyzed='false') + '\n'
            # Add layer relationships
            if index == 0:
                report = report + get_layer_relationships(layer_obj) + '\n'
            else:
                # block should contain previous layer dependency
                report = report + get_layer_relationships(
                    layer_obj, get_layer_spdxref(image_obj.layers[index - 1]))\
                    + '\n'

        # Add the package part for each package
        # There are no relationships to be listed here
        for layer_obj in image_obj.layers:
            for package_obj in layer_obj.packages:
                package_dict = package_obj.to_dict(template)
                # update the PackageLicenseDeclared with a LicenseRef string
                if 'PackageLicenseDeclared' in package_dict.keys():
                    package_dict['PackageLicenseDeclared'] = format_license(
                        package_obj.pkg_license)
                # collect all the individual licenses
                update_license_list(licenses_found, package_obj.pkg_license)
                report = report + get_main_block(
                    package_dict,
                    package_obj.origins.origins,
                    SPDXID=get_package_spdxref(package_obj),
                    PackageLicenseConcluded='NOASSERTION',
                    FilesAnalyzed='false') + '\n'
        return report + get_license_block(licenses_found)
