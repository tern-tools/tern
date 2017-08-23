'''
Docker metadata related modules
NOTE: these modules work on a temp folder to which the output of docker save
has already been extracted into
'''
import json
import os
import shutil

from commands import pushd
import constants

# docker manifest file
manifest_file = 'manifest.json'


def clean_temp():
    '''Remove the temp directory'''
    temp_path = os.path.abspath(constants.temp_folder)
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


def get_image_manifest():
    '''Assuming that there is a temp folder with a manifest.json of
    an image inside, get a dict of the manifest.json file'''
    temp_path = os.path.abspath(constants.temp_folder)
    with pushd(temp_path):
        with open(manifest_file) as f:
            json_obj = json.loads(f.read())
    return json_obj
