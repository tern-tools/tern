# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
OpossumUI Generator document
"""

import json
import logging

from tern.formats.spdx import spdx_common
from tern.utils.general import get_git_rev_or_version
from tern.utils import constants
from tern.formats import generator
from tern.report import content


# global logger
logger = logging.getLogger(constants.logger_name)


def get_resources(image_obj):
    '''Packages in each layer will be mapped to:
        /Layer_00x/Packages/pkg_source/pkg_name'''
    resources = {}
    for layer in image_obj.layers:
        resources["Layer_{}".format('%03d' % layer.layer_index)] = \
            {"Packages": {pkg.source: {
                p.name: 1 for p in layer.packages if p.source == pkg.source}
                for pkg in layer.packages}}
    return resources


def get_external_attrs(image_obj):
    '''Create a dict which contains attribution information about a file or
    folder. The key is the uuid of the package and the value is a dictionary
    of metadata'''
    external_attrs = {}
    image_uuids = {}
    for layer in image_obj.layers:
        for pkg in layer.packages:
            pkg_uuid = spdx_common.get_uuid()
            if layer.layer_index in image_uuids.keys():
                try:
                    # See if source exists in layer
                    image_uuids[layer.layer_index][pkg.source].append(pkg_uuid)
                except KeyError:
                    # If not, add the new source to existing layer
                    image_uuids[layer.layer_index][pkg.source] = [pkg_uuid]
            else:
                # add new layer and source
                image_uuids[layer.layer_index] = {pkg.source: [pkg_uuid]}
            pkg_comment = ''
            if pkg.origins.origins:
                for notice_origin in pkg.origins.origins:
                    pkg_comment = pkg_comment + content.print_notices(
                        notice_origin, '', '\t')
            # Debian will have a pkg_licenses value but not license
            pkg_license = pkg.pkg_license if pkg.pkg_license else \
                ''.join(pkg.pkg_licenses)
            external_attrs[pkg_uuid] = {
                "source": {
                    "name": pkg.source,
                    "documentConfidence": int(70.0)
                },
                "comment": pkg_comment,
                "packageName": pkg.name,
                "packageVersion": pkg.version if pkg.version else "NONE",
                "url": pkg.proj_url,
                "licenseName": pkg_license if pkg_license else "NONE",
                "copyright": pkg.copyright if pkg.copyright else "NONE"
            }
    return external_attrs, image_uuids


def get_resource_attrs(uuids):
    '''Return the dictionary that maps a [package] path in the resource tree
    to a list of externalAttribution uuid string(s):
        {"/path/to/resource/": [<list of resource uuids>]}'''
    resource_attrs = {}
    for layer, layer_uuids in uuids.items():
        for source, pkg_uuids in layer_uuids.items():
            resource_attrs["/Layer_{}/Packages/{}/".format(
                '%03d' % layer, source)] = pkg_uuids
    return resource_attrs


def get_attr_breakpoints(image_obj):
    '''We list pacakges in each layer under the Layer_00x/Packages/source
    directory but that is not the literal path. Hence, we add
    Layer_00x/Packages/ for each layer as an attribution breakpoint.
    '''
    attr_breakpoints = []
    for layer in image_obj.layers:
        attr_breakpoints.append("/Layer_{}/Packages/".format(
            '%03d' % layer.layer_index))
    return attr_breakpoints


def get_document_dict(image_obj):
    '''Return a dictionary that maps the following fields:
        metadata: containers project-level information
        resources: defines the file tree
        externalAttributions: contains attributions provided as signals
        resourcesToAttributions: links attributions to file paths
        attributionBreakpoints: Folders where the attribution inference stops.
        '''
    docu_dict = {
        "metadata": {
            "projectId": get_git_rev_or_version()[1],
            "projectTitle": "Tern report for {}".format(image_obj.name),
            "fileCreationDate": spdx_common.get_timestamp()
        }
    }

    docu_dict["resources"] = get_resources(image_obj)
    docu_dict["externalAttributions"], uuids = get_external_attrs(image_obj)
    docu_dict["resourcesToAttributions"] = get_resource_attrs(uuids)
    docu_dict["attributionBreakpoints"] = get_attr_breakpoints(image_obj)
    return docu_dict


class OpossumUI(generator.Generate):
    def generate(self, image_obj_list, print_inclusive=False):
        logger.debug("Generating OpossumUI document...")
        image_obj = image_obj_list[0]
        report = get_document_dict(image_obj)
        return json.dumps(report)
