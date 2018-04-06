'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''


import os
import yaml
from .constants import cache_file
'''
Docker layer cache related modules
The cache is currently stored in a yaml file called cache.yml
It is organized in this way:
    layer sha:
        packages:
           - name:
             version:
             license:
             src_url:
        .....
'''

# known base image database
cache = {}


def load():
    '''Load the cache'''
    global cache
    with open(os.path.abspath(cache_file)) as f:
        cache = yaml.load(f)


def get_packages(sha):
    '''Given an image sha retrieve cache record. If none return an empty
    list'''
    if sha in cache.keys():
        return cache[sha]['packages']
    else:
        return []


def get_layers():
    '''Return a list of layer shas'''
    return cache.keys()


def add_layer(layer_obj):
    '''Given a layer object, add it to the cache'''
    cache.update(layer_obj.to_dict())


def save():
    '''Given a layer object record it into the cache'''
    with open(os.path.abspath(cache_file), 'w') as f:
        yaml.dump(cache, f, default_flow_style=False)


def remove_layer(sha):
    '''Remove from cache the layer represented by the sha'''
    success = False
    if sha in cache.keys():
        del cache[sha]
        success = True
    return success


def clear():
    '''Empty the cache - don't use unless you really have to_dict'''
    global cache
    cache = {}
    with open(os.path.abspath(cache_file), 'w') as f:
        yaml.dump(cache, f, default_flow_style=False)
