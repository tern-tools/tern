# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
OCI specific functions - used when trying to retrieve packages when
given a OCI Image
"""

import os
import re
import json
from tern.report import errors
from tern.analyze import common
from tern.report import formats
from tern.classes.notice import Notice

directives = ['FROM',
              'ARG',
              'ADD',
              'RUN',
              'ENV',
              'COPY',
              'ENTRYPOINT',
              'WORKDIR',
              'VOLUME',
              'EXPOSE',
              'CMD']


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


def created_to_instruction(created_by):
    '''The 'created_by' key in a OCI image config gives the shell
    command that was executed unless it is a #(nop) instruction which is
    for the other directives. Convert this line into a instruction
    '''
    instruction = re.sub('/bin/sh -c ', '', created_by).strip()
    instruction = re.sub(re.escape('#(nop) '), '', instruction).strip()
    first = instruction.split(' ').pop(0)
    if first and first not in directives and \
            'RUN' not in instruction:
        instruction = 'RUN ' + instruction
    return instruction


def get_commands_from_history(image_layer):
    '''Given the image layer object and the shell, get the list of command
    objects that created the layer'''
    # set up notice origin for the layer
    origin_layer = 'Layer: ' + image_layer.fs_hash[:10]
    if image_layer.created_by:
        instruction = created_to_instruction(image_layer.created_by)
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.oci_image_line.format(oci_image_instruction=instruction),
            'info'))
        command_line = instruction.split(' ', 1)[1]
    else:
        instruction = ''
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            formats.no_created_by, 'warning'))
        command_line = instruction
    # Image layers are created with the directives RUN, ADD and COPY
    # For ADD and COPY instructions, there is no information about the
    # packages added
    if 'ADD' in instruction or 'COPY' in instruction:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            errors.unknown_content.format(files=command_line), 'warning'))
        # return an empty list as we cannot find any commands
        return []
    # for RUN instructions we can return a list of commands
    command_list, msg = common.filter_install_commands(command_line)
    if msg:
        image_layer.origins.add_notice_to_origins(origin_layer, Notice(
            msg, 'warning'))
    return command_list
