'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import json
import os
import re

from utils.general import pushd
from utils.constants import temp_folder
from utils.constants import manifest_file
from utils.container import extract_image_metadata
from utils.dockerfile import directives

from .image_layer import ImageLayer
from .image import Image


class DockerImage(Image):
    '''A representation of an image created by Docker
    See image.py for super class's attributes'''
    def __init__(self, repotag=None, id=None):
        '''Use superclass's attributes'''
        super().__init__(repotag, id)

    def get_image_manifest(self):
        '''Assuming that there is a temp folder with a manifest.json of
        an image inside, get a dict of the manifest.json file'''
        temp_path = os.path.abspath(temp_folder)
        with pushd(temp_path):
            with open(manifest_file) as f:
                json_obj = json.loads(f.read())
        return json_obj

    def get_image_layers(self, manifest):
        '''Given the manifest, return the layers'''
        layers = []
        for layer in manifest[0].get('Layers'):
            layers.append(layer)
        return layers

    def get_image_config_file(self, manifest):
        '''Given the manifest, return the config file'''
        return manifest[0].get('Config')

    def get_image_id(self, manifest):
        '''Given the manifest, return the image id
        This happens to be the config file's sha256sum'''
        config_file = self.get_image_config_file(manifest)
        return config_file.split('.')[0]

    def get_image_repotags(self, manifest):
        '''Given the manifest, return the list of image tag strings'''
        return manifest[0].get('RepoTags')

    def get_layer_sha(layer_path):
        '''Docker's layers are file paths starting with the ID.
        Get just the sha'''
        return os.path.dirname(layer_path)

    def get_image_config(self, manifest):
        '''Assuming there now exists a working directory where the image
        metadata exists, return the image config'''
        config_file = self.get_image_config_file(manifest)
        # assuming that the config file path is in the same root path as the
        # manifest file
        temp_path = os.path.abspath(temp_folder)
        with pushd(temp_path):
            with open(config_file) as f:
                json_obj = json.loads(f.read())
        return json_obj

    def get_image_history(self, config):
        '''If the config has the image history return it. Else return None'''
        if 'history' in config.keys():
            return config['history']
        else:
            return None

    def get_diff_ids(self, config):
        '''Given the image config, return the filesystem diff ids'''
        diff_ids = []
        for item in config['rootfs']['diff_ids']:
            diff_ids.append(item.split(':').pop())
        return diff_ids

    def set_layer_created_by(self):
        '''Docker image history configuration consists of a list of commands
        and indication of whether the command created a filesystem or not.
        Set the created_by for each layer in the image'''
        # the history is ordered according to the order of the layers
        # so the first non-empty history corresponds with the first layer
        index = 0
        for item in self._history:
            if 'empty_layer' not in item.keys():
                if 'created_by' in item.keys():
                    self._layers[index].created_by = item['created_by']
                else:
                    self._layers[index].created_by = ''
                index = index + 1

    def load_image(self):
        '''Load image metadata using docker commands'''
        try:
            option = self.get_image_option()
            if extract_image_metadata(option):
                print('Image extracted')
            else:
                print('Failed to extract image')
            self._manifest = self.get_image_manifest()
            self._id = self.get_image_id(self._manifest)
            self._repotags = self.get_image_repotags(self._manifest)
            self._config = self.get_image_config(self._manifest)
            self._history = self.get_image_history(self._config)
            layer_paths = self.get_image_layers(self._manifest)
            layer_diffs = self.get_diff_ids(self._config)
            while layer_diffs and layer_paths:
                layer = ImageLayer(layer_diffs.pop(0), layer_paths.pop(0))
                self._layers.append(layer)
            self.set_layer_created_by()
        except NameError as error:
            print(error)
            raise NameError(error)

    def created_to_instruction(self, created_by):
        '''The 'created_by' key in a Docker image config gives the shell
        command that was executed unless it is a #(nop) instruction which is
        for the other Docker directives. Convert this line into a Dockerfile
        instruction'''
        instruction = re.sub('/bin/sh -c', '', created_by).strip()
        instruction = re.sub('\#\(nop\)', '', instruction).strip()
        first = instruction.split(' ').pop(0)
        if first in directives and 'RUN' not in instruction:
            instruction = 'RUN ' + instruction
        return instruction
