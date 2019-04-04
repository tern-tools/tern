#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

from tern.classes.origins import Origins


class Image:
    '''A representation of the image to be analyzed
    attributes:
        id: this is a unique identifier for the image - for OCI spec this could
        be the digest. For now this is the sha256sum of the config.json
        manifest: the json object representing the image manifest
        config: the image config metadata
        layers: list of layer objects in the image
    methods:
        load_image: this method is to be implemented in the derived classes
        get_layer_diff_ids: returns a list of layer diff ids only
        to_dict: return a python dictionary representation of the image
    '''
    def __init__(self, id=None):  # pylint: disable=redefined-builtin
        '''Either initialize using id'''
        self._id = id
        self._name = ''
        self._tag = ''
        self._manifest = {}
        self._config = {}
        self._layers = []
        self._origins = Origins()

    @property
    def manifest(self):
        return self._manifest

    @property
    def id(self):
        return self._id

    @property
    def config(self):
        return self._config

    @property
    def layers(self):
        return self._layers

    @property
    def origins(self):
        return self._origins

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, tag):
        self._tag = tag

    def get_layer_diff_ids(self):
        '''Get a list of layer diff ids'''
        return [layer.diff_id for layer in self.layers]

    def set_image_import(self, imported_image):
        '''If this image is created on top of a given imported image, set this
        image's layer's import_image to the last layer of the imported image.
        return True if the imported_image's last layer exists in this image.
        False if it does not'''
        is_set = True
        if imported_image.layers:
            imported_layer = self.get_layer_object(
                imported_image.layers[-1].diff_id)
            if imported_layer:
                imported_layer.import_image = imported_image
            else:
                is_set = False
        else:
            is_set = False
        return is_set

    def get_last_import_layer(self):
        '''Get the index of the last layer that was brought in from
        an imported image'''
        for layer in self.layers[::-1]:
            if layer.import_image:
                return self.layers.index(layer)
        return None

    def get_layer_object(self, diff_id):
        '''Given a layer diff id, return the layer object that contains this
        diff id'''
        for layer in self.layers:
            if layer.diff_id == diff_id:
                return layer
        return None

    def load_image(self):
        '''Load image metadata
        Currently there is no standard way to do this. For a specific tool,
        Inherit from this class and override this method'''
        pass

    def to_dict(self):
        '''Return a dictionary representation of the image'''
        d = {'id': self.id,
             'name': self.name,
             'tag': self.tag,
             'manifest': self.manifest,
             'config': self.config,
             'layers': [layer.to_dict() for layer in self.layers],
             'notes': self.origins.to_dict()
             }
        return d
