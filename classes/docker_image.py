'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

from utils import container
from utils import metadata
from .image_layer import ImageLayer
from .image import Image


class DockerImage(Image):
    '''A representation of an image created by Docker
    See image.py for super class's attributes'''
    def __init__(self, repotag=None, id=None):
        '''Use superclass's attributes'''
        super().__init__(repotag, id)

    def load_image(self):
        '''Load image metadata using docker commands'''
        try:
            option = self.get_image_option()
            if container.extract_image_metadata(option):
                print('Image extracted')
            else:
                print('Failed to extract image')
            self._manifest = metadata.get_image_manifest()
            self._id = metadata.get_image_id(self._manifest)
            self._repotags = metadata.get_image_repotags(self._manifest)
            self._config = metadata.get_image_config(self._manifest)
            self._history = metadata.get_image_history(self._config)
            layer_paths = metadata.get_image_layers(self._manifest)
            layer_diffs = metadata.get_diff_ids(self._config)
            while layer_diffs and layer_paths:
                layer = ImageLayer(layer_diffs.pop(0), layer_paths.pop(0))
                self._layers.append(layer)
        except NameError as error:
            print(error)
            raise NameError(error)
