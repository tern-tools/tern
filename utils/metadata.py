'''
Docker metadata related modules
NOTE: these modules work on a temp folder to which the output of docker save
has already been extracted into
'''
import json
import os
import shutil

from utils.commands import pushd
import utils.constants as const

# docker manifest file
manifest_file = 'manifest.json'


def clean_temp():
    '''Remove the temp directory'''
    temp_path = os.path.abspath(const.temp_folder)
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


def get_image_manifest():
    '''Assuming that there is a temp folder with a manifest.json of
    an image inside, get a dict of the manifest.json file'''
    temp_path = os.path.abspath(const.temp_folder)
    with pushd(temp_path):
        with open(manifest_file) as f:
            json_obj = json.loads(f.read())
    return json_obj


def get_image_layers(manifest):
    '''Given the manifest, return the layers'''
    return manifest[0].get('Layers')


def get_image_config(manifest):
    '''Given the manifest, return the config file'''
    return manifest[0].get('Config')


def get_image_repotags(manifest):
    '''Given the manifest, return the list of image tag strings'''
    return manifest[0].get('RepoTags')


def get_layer_sha(layer_path):
    '''Docker's layers are file paths starting with the ID.
    Get just the sha'''
    return os.path.dirname(layer_path)
