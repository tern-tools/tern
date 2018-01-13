'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

from utils import container
from utils import metadata
from .image_layer import ImageLayer


class Image(object):
    '''A representation of the image to be analyzed
    attributes:
        repotag: the repotag used to reference the image
        id: this is a unique identifier for the image - for OCI spec this could
        be the digest. For now this is the sha256sum of the config.json in a
        Docker compatible manifest
        manifest: the json object representing the image manifest
        repotags: the list of repotags associated with this image
        config: the image config metadata
        layers: list of layer objects in the image
        history: a list of commands used to create the filesystem layers
        This is used in Docker images to match Dockerfiles but is an optional
        part of OCI compatible images
    methods:
        load_image: this method uses the metadata utility to load all
        the metadata for the image
    '''
    def __init__(self, repotag=None, id=None):
        '''Either initialize using the repotag or the id'''
        self.__repotag = repotag
        self.__id = id
        self.__manifest = {}
        self.__repotags = []
        self.__config = {}
        self.__layers = []
        self.__history = None

    @property
    def repotag(self):
        return self.__repotag

    @property
    def manifest(self):
        return self.__manifest

    @property
    def id(self):
        return self.__id

    @property
    def repotags(self):
        return self.__repotags

    @property
    def config(self):
        return self.__config

    @property
    def layers(self):
        return self.__layers

    @property
    def history(self):
        return self.__history

    def get_layer_diff_ids(self):
        '''Get a list of layer diff ids'''
        return [layer.diff_id for layer in self.layers]

    def get_image_option(self):
        '''Check to see which value was used to init the image object
        Return the value that was used. If neither one was used raise
        NameError. If both were used return the id'''
        if self.repotag is not None and self.id is not None:
            return self.id
        elif self.repotag is not None:
            return self.repotag
        elif self.id is not None:
            return self.id
        else:
            raise NameError("Image object initialized with no repotag or ID")

    def load_image(self):
        '''Load image metadata based on the image build tool
        There is no standard format and there are several tools used to build
        container images. For now only docker save is supported
        '''
        try:
            option = self.get_image_option()
            if container.extract_image_metadata(option):
                print('Image extracted')
            else:
                print('Failed to extract image')
            self.__manifest = metadata.get_image_manifest()
            self.__id = metadata.get_image_id(self.__manifest)
            self.__repotags = metadata.get_image_repotags(self.__manifest)
            self.__config = metadata.get_image_config(self.__manifest)
            self.__history = metadata.get_image_history(self.__config)
            layer_paths = metadata.get_image_layers(self.__manifest)
            layer_diffs = metadata.get_diff_ids(self.__config)
            while layer_diffs and layer_paths:
                layer = ImageLayer(layer_diffs.pop(0), layer_paths.pop(0))
                self.__layers.append(layer)
        except NameError as error:
            print(error)
            raise NameError(error)
