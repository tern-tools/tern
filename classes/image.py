'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''


class Image(object):
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
        get_image_option: returns whether the image object was instantiated
        using the repotag or id
    '''
    def __init__(self, id=None):
        '''Either initialize using id'''
        self._id = id
        self._name = ''
        self._tag = ''
        self._manifest = {}
        self._config = {}
        self._layers = []
        self._notices = []

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
    def notices(self):
        return self._notices

    @property
    def name(self):
        return self._name

    @property
    def tag(self):
        return self._tag

    def add_notice(self, notice):
        self._notices.append(notice)

    def get_layer_diff_ids(self):
        '''Get a list of layer diff ids'''
        return [layer.diff_id for layer in self.layers]

    def load_image(self):
        '''Load image metadata
        Currently there is no standard way to do this. For a specific tool,
        Inherit from this class and override this method'''
        pass
