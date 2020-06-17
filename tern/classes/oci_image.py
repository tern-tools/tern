# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import os
import re
import json
import subprocess  # nosec
from tern.utils import general
from tern.classes.image import Image
from tern.analyze.oci import helpers
from tern.classes.image_layer import ImageLayer


class OCIImage(Image):
    '''A representation of an image created using OCI format
    See image.py for super class's attributes
    OCI Image specific attributes:
        repotag: the repotag associated with this image
        history: a list of commands used to create the filesystem layers
        to_dict: return a dict representation of the object
    '''

    def __init__(self, repotag=None):
        super().__init__(repotag)
        self.__history = None
        if self.repotag is None:
            raise NameError("Image object initialized with no repotag")

        # parse the repotag
        repo_dict = general.parse_oci_image_string(self._repotag)
        self._name = repo_dict.get('name')
        self._tag = repo_dict.get('tag')
        self._image_path = repo_dict.get('path')

    @property
    def history(self):
        return self.__history

    @property
    def image_path(self):
        return self._image_path

    @image_path.setter
    def image_path(self, image_path):
        self._image_path = image_path

    def to_dict(self, template=None):
        '''Return a dictionary representation of the OCI image'''
        # this should take care of 'origins' and 'layers'
        di_dict = super().to_dict(template)
        return di_dict

    def get_image_index(self):
        '''Returns OCI image index data'''
        index_path = os.path.join(self.image_path, "index.json")
        with open(index_path) as f:
            return json.load(f)

    def get_image_manifest(self, image_index):
        '''Given image index, returns image manifest'''
        manifest = image_index.get("manifests")[0].get("digest")
        manifest = re.split(r'[:]', manifest)[1]
        manifest = 'blobs/sha256/{0}'.format(manifest)
        manifest = os.path.join(self.image_path, manifest)
        with open(manifest) as f:
            return json.load(f)

    def get_image_layers(self, manifest):
        '''Given the manifest, return the layers'''
        layers = []
        for layer in manifest.get('layers'):
            layers.append(layer.get("digest").split(":")[1])
        return layers

    def get_image_config_file(self, manifest):
        '''Given the manifest, return the config file'''
        return manifest.get('config').get("digest").split(":")[1]

    def get_layer_sha(self, layer_path):
        '''OCI's layers are file paths starting with the ID.
        Get just the sha'''
        return os.path.dirname(layer_path)

    def get_image_config(self, manifest):
        '''Given the manifest, returns the config data'''
        config_file = self.get_image_config_file(manifest)
        config_file = 'blobs/sha256/{0}'.format(config_file)
        config_file = os.path.join(self.image_path, config_file)
        with open(config_file) as f:
            return json.load(f)

    def get_image_history(self, config):
        '''If the config has the image history return it. Else return None'''
        return config.get('history', None)

    def get_diff_checksum_type(self, image_index):
        '''Given image index, returns image checksum type'''
        manifest = image_index.get("manifests")[0].get("digest")
        return re.split(r'[:]', manifest)[0]

    def set_layer_created_by(self):
        '''OCI image history configuration consists of a list of commands
        and indication of whether the command created a filesystem or not.
        Set the created_by for each layer in the image'''
        # the history is ordered according to the order of the layers
        # so the first non-empty history corresponds with the first layer
        index = 0
        for item in self.__history:
            if 'empty_layer' not in item.keys():
                if 'created_by' in item.keys():
                    self._layers[index].created_by = item['created_by']
                else:
                    self._layers[index].created_by = ''
                index = index + 1

    def load_image(self):
        '''Load OCI image metadata using manifest'''
        try:
            # validate OCI iamge's directory layout
            helpers.validate_image_path(self.image_path)
            image_index = self.get_image_index()
            self._manifest = self.get_image_manifest(image_index)
            self._config = self.get_image_config(self._manifest)
            self.__history = self.get_image_history(self._config)
            layer_paths = self.get_image_layers(self._manifest)
            # copy image layers to working dir for further analysis
            helpers.copy_oci_image_layers(self.image_path, layer_paths)
            checksum_type = self.get_diff_checksum_type(image_index_data)
            while layer_paths:
                layer = ImageLayer(None, layer_paths.pop(0))
                layer.set_checksum(checksum_type, layer.diff_id)
                layer.gen_fs_hash()
                self._layers.append(layer)
            self.set_layer_created_by()
        except NameError:  # pylint: disable=try-except-raise
            raise
        except subprocess.CalledProcessError:  # pylint: disable=try-except-raise
            raise
        except IOError:  # pylint: disable=try-except-raise
            raise
        except Exception:
            raise
