# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import os
import json
import subprocess  # nosec
from tern.utils import rootfs
from tern.utils import general
from tern.classes.image import Image
from tern.utils.constants import manifest_file
from tern.classes.image_layer import ImageLayer


class OCIImage(Image):
    def __init__(self, repotag=None, image_id=None):
        super().__init__(image_id)
        self.__repotag = repotag

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
        # this should take care of 'origins' and 'layers'
        di_dict = super().to_dict(template)
        return di_dict

    def get_image_option(self):
        if self.repotag is not None and self.image_id is not None:
            return self.image_id
        if self.repotag is not None:
            return self.repotag
        if self.image_id is not None:
            return self.image_id
        raise NameError("Image object initialized with no repotag or ID")

    def get_image_manifest(self):
        temp_path = rootfs.get_working_dir()
        with general.pushd(temp_path):
            with open(manifest_file) as f:
                json_obj = json.loads(f.read())
        return json_obj

    def get_image_layers(self, manifest):
        layers = []
        for layer in manifest.get('layers'):
            layers.append(layer.get("digest").split(":")[1])
        return layers

    def get_image_config_file(self, manifest):
        return manifest.get('config').get("digest").split(":")[1]

    def get_image_id(self, manifest):
        config_file = self.get_image_config_file(manifest)
        return config_file

    def get_image_repotags(self):
        temp_path = rootfs.get_working_dir()
        annotations = None
        with general.pushd(temp_path):
            with open("index.json") as f:
                json_obj = json.loads(f.read())
                annotations = json_obj.get("manifests")[0].get("annotations")
        return annotations.get("org.opencontainers.image.ref.name")

    def get_layer_sha(self, layer_path):
        return os.path.dirname(layer_path)

    def get_image_config(self, manifest):
        config_file = self.get_image_config_file(manifest)
        temp_path = rootfs.get_working_dir()
        with general.pushd(temp_path):
            with open(config_file) as f:
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
                if 'created_by' in item.keys():
                    self._layers[index].created_by = item['created_by']
                else:
                    self._layers[index].created_by = ''
                index = index + 1

    def load_image(self):
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
        except NameError:  # pylint: disable=try-except-raise
            raise
        except subprocess.CalledProcessError:  # pylint: disable=try-except-raise
            raise
        except IOError:  # pylint: disable=try-except-raise
            raise
{"mode":"full","isActive":false}
