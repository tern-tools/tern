import os
import yaml
'''
Docker image and layer related modules
NOTE: the cache contains base image information
currently there is no way to step through docker history
So the assumption is that the base image is a flat image (which it is not)
For now we will run commands within the whole base image based on the
Dockerfile, but ideally we need to step through the base image history and
find the actual base image
'''

# known base image database
cache_file = 'cache.yml'
cache = {}


def load():
    '''Load the cache'''
    with open(os.path.abspath(cache_file)) as f:
        global cache
        cache = yaml.load(f)
    if cache is not None:
        global cache
        cache = {}


def get_packages(sha):
    '''Given an image sha retrieve cache record. If none return an empty list'''
    if sha in cache.keys():
        return cache[sha]
    else:
        return []


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
        global cache
        yaml.dump(cache, f, default_flow_style=False)
