# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
OCI specific functions - used when trying to retrieve packages when
given a OCI Image
"""

import os
# import re
import json
# from tern.report import errors
# from tern.analyze import common
# from tern.report import formats
# from tern.classes.notice import Notice


def get_oci_image_index(image_string):
    ''' Returns OCI image index path '''
    return os.path.join(image_string, "index.json")


def get_oci_image_manifest(image_string):
    ''' Returns OCI image manifest path '''
    blob_path = os.path.join(image_string, "blobs/sha256")
    index_json = json.load(open(get_oci_image_index(image_string)))
    manifest_digest = index_json.get(
        "manifests")[0].get("digest").split(":")[1]
    return os.path.join(blob_path, manifest_digest)


def get_oci_image_config(image_string, manifest):
    ''' Returns OCI image config path '''
    blob_path = os.path.join(image_string, "blobs/sha256")
    config_digest = json.load(open(manifest)).get(
        "config").get("digest").split(":")[1]
    return os.path.join(blob_path, config_digest)


def get_oci_image_layers(image_string, manifest):
    ''' Returns OCI image layers '''
    blob_path = os.path.join(image_string, "blobs/sha256")
    layers = list()
    layer_data = json.load(open(manifest)).get("layers")
    for layer in layer_data:
        layer_path = os.path.join(blob_path, layer.get("digest").split(":")[1])
        layers.append(layer_path)
    return layers
