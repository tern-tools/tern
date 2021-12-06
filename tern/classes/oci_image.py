# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import json
import subprocess  # nosec

from tern.utils import rootfs
from tern.utils import general
from tern.classes.image import Image
from tern.utils.constants import manifest_file
from tern.classes.image_layer import ImageLayer


class OCIImage(Image):
    """A representation of an OCI compatible image that exists on disk"""
    def __init__(self, repotag=None):
        super().__init__(repotag)
        # In case the OCI image corresponds with an image built by Docker
        # we also include the history
        self.__history = None
        if self.repotag is None:
            raise NameError("Image object initialized with no repotag")

        # parse the repotag
        repo_dict = general.parse_image_string(self._repotag)
        self._name = repo_dict.get('name')
        self._tag = repo_dict.get('tag')
        self.set_checksum(
            repo_dict.get('digest_type'), repo_dict.get('digest'))

    @property
    def history(self):
        return self.__history

    def to_dict(self, template=None):
        # this should take care of 'origins' and 'layers'
        oci_dict = super().to_dict(template)
        return oci_dict

    def get_image_manifest(self):
        temp_path = rootfs.get_working_dir()
        with general.pushd(temp_path):
            with open(manifest_file, encoding='utf-8') as f:
                json_obj = json.loads(f.read())
        return json_obj

    def get_image_layers(self, manifest):
        layers = []
        for layer in manifest.get('layers'):
            layers.append(layer.get("digest").split(":")[1])
        return layers

    def get_image_config_file(self, manifest):
        return manifest.get('config').get("digest").split(":")[1]

    def get_image_config(self, manifest):
        config_file = self.get_image_config_file(manifest)
        temp_path = rootfs.get_working_dir()
        with general.pushd(temp_path):
            with open(config_file, encoding='utf-8') as f:
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
        '''Get the checksum type that was used to calculate the diff_id
        of the image'''
        return config['rootfs']['diff_ids'][0].split(':')[0]

    def set_layer_created_by(self):
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

    def load_image(self, load_until_layer=0):
        if load_until_layer > 0:
            self._load_until_layer = load_until_layer
        try:
            self._manifest = self.get_image_manifest()
            self._config = self.get_image_config(self._manifest)
            self.__history = self.get_image_history(self._config)
            layer_paths = self.get_image_layers(self._manifest)
            layer_diffs = self.get_diff_ids(self._config)
            # if the digest isn't in the repotag, get it from the config
            if not self.checksum:
                repo_dict = general.parse_image_string(
                    self._config.get("config").get("Image"))
                self.set_checksum(repo_dict.get("digest_type"),
                                  repo_dict.get("digest"))
            layer_checksum_type = self.get_diff_checksum_type(self._config)
            layer_count = 1
            while layer_diffs and layer_paths:
                layer = ImageLayer(layer_diffs.pop(0), layer_paths.pop(0))
                if (self.load_until_layer >= layer_count
                        or self.load_until_layer == 0):
                    layer.set_checksum(layer_checksum_type, layer.diff_id)
                    layer.image_layout = "oci"
                    # take care to set the layer index as it will be used
                    # to create the directory where the layer contents will
                    # be untarred
                    layer.layer_index = layer_count
                    layer.gen_fs_hash()
                    self._layers.append(layer)
                layer_count = layer_count + 1
            self._total_layers = layer_count - 1
            if self.load_until_layer > self.total_layers:
                # if user asked to analyze more layers than image has
                # turn off the load_until_layer feature
                self._load_until_layer = 0
            self.set_layer_created_by()
        except NameError as e:
            raise NameError(e) from e
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError(
                e.returncode, cmd=e.cmd, output=e.output, stderr=e.stderr)
        except IOError as e:
            raise IOError(e) from e
