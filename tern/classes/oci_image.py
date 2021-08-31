# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import os
import json
import subprocess  # nosec
from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer


class OCIImage(Image):
    '''A representation of an image created by OCI
    See image.py for super class's attributes
    OCI Image specific attributes:
        repotags: the list of repotags associated with this image
        history: a list of commands used to create the filesystem layers
        to_dict: return a dict representation of the object
    '''
    def __init__(self, repotag=None):
        '''Initialize using repotag'''
        super().__init__(repotag)
        self.__repotag = repotag.split('oci://')[1]
        if self.repotag is None:
            raise NameError("Image object initialized with no repotag")

    @property
    def repotag(self):
        return self.__repotag

    @property
    def repotags(self):
        return self.__repotags

    @property
    def history(self):
        return self.__history

    def to_dict(self, template=None):
        '''Return a dictionary representation of the OCI image'''
        di_dict = super().to_dict(template)
        return di_dict

    def get_image_manifest(self):
        ''' Returns OCI image manifest path '''
        blob_path = os.path.join(self.repotag, "blobs/sha256")
        manifest_digest = ''
        with open(os.path.join(self.repotag, "index.json"), encoding="UTF-8") as f:
            index_json = json.load(f)
            manifest_digest = index_json.get("manifests")
            if not manifest_digest:
                raise Exception("manifest is missing")
            manifest_digest = manifest_digest[0].get("digest").split(":")[1]

        return os.path.join(blob_path, manifest_digest)

    def get_image_layers(self, manifest):
        ''' Returns OCI image layers '''
        blob_path = os.path.join(self.repotag, "blobs/sha256")
        layers = []
        with open(manifest, encoding="UTF-8") as f:
            layer_data = json.load(f).get("layers")
            for layer in layer_data:
                layer_path = os.path.join(
                    blob_path, layer.get("digest").split(":")[1])
                layers.append(layer_path)

        return layers

    def get_image_config_file(self, manifest):
        ''' Returns OCI image config path '''
        blob_path = os.path.join(self.repotag, "blobs/sha256")
        config_digest = ''
        with open(manifest, encoding="UTF-8") as f:
            config = json.load(f).get("config")
            config_digest = config.get("digest").split(":")[1]

        return os.path.join(blob_path, config_digest)

    def get_image_repotags(self):
        return ''

    def get_layer_sha(self, layer_path):
        return os.path.dirname(layer_path)

    def get_image_config(self, manifest):
        config_file = self.get_image_config_file(manifest)
        json_obj = ''
        with open(config_file, encoding="UTF-8") as f:
            json_obj = json.loads(f.read())
        return json_obj

    def get_image_history(self, config):
        if 'history' in config.keys():
            return config['history']
        return None

    def get_diff_ids(self, config):
        diff_ids = []
        for item in config['rootfs']['diff_ids']:
            diff_ids.append(item.split(':').pop())
        return diff_ids

    def get_diff_checksum_type(self, config):
        return config['rootfs']['diff_ids'][0].split(':')[0]

    def set_layer_created_by(self):
        # the history is ordered according to the order of the layers
        # so the first non-empty history corresponds with the first layer
        index = 0
        for item in self.__history:
            if 'empty_layer' not in item.keys():
                self._layers[index].created_by = ''
                if 'created_by' in item.keys():
                    self._layers[index].created_by = item['created_by']
                index = index + 1
                if index is self.load_until_layer:
                    break

    def load_image(self, load_until_layer=0):
        """Load metadata from an extracted OCI image. This assumes the
        image has already been downloaded and extracted into the working
        directory"""
        if load_until_layer > 0:
            self._load_until_layer = load_until_layer
        # else defaults to 0 - handles negative load_until_layer
        try:
            self._manifest = self.get_image_manifest()
            self._image_id = self.get_image_id(self._manifest)
            self.__repotags = self.get_image_repotags()
            self._config = self.get_image_config(self._manifest)
            self.__history = self.get_image_history(self._config)
            layer_paths = self.get_image_layers(self._manifest)
            layer_diffs = self.get_diff_ids(self._config)
            checksum_type = self.get_diff_checksum_type(self._config)
            while layer_diffs and layer_paths:
                layer = ImageLayer(layer_diffs.pop(0), layer_paths.pop(0))
                layer.set_checksum(checksum_type, layer.diff_id)
                layer.gen_fs_hash()
                self._layers.append(layer)
            self.set_layer_created_by()
        except NameError as e:
            raise NameError(e) from e
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError(
                e.returncode, cmd=e.cmd, output=e.output, stderr=e.stderr)
        except IOError as e:
            raise IOError(e) from e
