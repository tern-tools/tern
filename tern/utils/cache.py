# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Docker layer cache related modules
The cache is currently stored in a yaml file called cache.yml
It is organized in this way:
    layer sha:
        packages:
           - name:
             version:
             license:
             proj_url:
        .....
"""

import os
import json
from tern.utils.constants import cache_file
from tern.utils import rootfs

# known base image database
cache = {}


def load():
    '''Load the cache'''
    global cache

    # Do not try to populate the cache if there is no cache available
    if not os.path.exists(os.path.join(rootfs.working_dir, cache_file)):
        return

    with open(os.path.join(rootfs.working_dir, cache_file)) as f:
        cache = json.load(f)


def get_packages(layer_hash):
    '''Given the layer hash, retrieve cache record. If none return an empty
    list'''
    if layer_hash in cache.keys():
        return cache[layer_hash]['packages']
    return []


def get_files(layer_hash):
    '''Given the layer hash, retrieve file layers cache record.
    If none return an empty list'''
    if layer_hash in cache.keys():
        return cache[layer_hash]['files']
    return []


def get_layers():
    '''Return a list of layer shas'''
    return cache.keys()


def get_origins(layer_hash):
    '''Return the origins dictionary'''
    if layer_hash in get_layers():
        if 'origins' in cache[layer_hash].keys():
            return cache[layer_hash]['origins']
    return []


def add_layer(layer_obj):
    '''Given a layer object, add it to the cache
    We use the layer's to_dict object and make a dictionary such that
    the key is the layer object's fs_hash function and the value is the
    rest of the dictionary'''
    layer_dict = layer_obj.to_dict()
    fs_hash = layer_dict.pop('fs_hash')
    cache.update({fs_hash: layer_dict})


def save():
    '''Save the cache to the cache file'''
    with open(os.path.join(rootfs.working_dir, cache_file), 'w') as f:
        json.dump(cache, f)


def remove_layer(layer_hash):
    '''Remove from cache the object referenced by the layer hash'''
    success = False
    if layer_hash in cache.keys():
        del cache[layer_hash]
        success = True
    return success


def clear():
    '''Empty the cache - don't use unless you really have to'''
    global cache
    cache = {}
    with open(os.path.join(rootfs.working_dir, cache_file), 'w') as f:
        json.dump(cache, f)
