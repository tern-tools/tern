'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''


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
    methods:
        load_image: this method is to be implemented in the derived classes
        get_layer_diff_ids: returns a list of layer diff ids only
        get_image_option: returns whether the image object was instantiated
        using the repotag or id
    '''
    def __init__(self, repotag=None, id=None):
        '''Either initialize using the repotag or the id'''
        self._repotag = repotag
        self._id = id
        self._manifest = {}
        self._repotags = []
        self._config = {}
        self._layers = []
        self._history = None

    @property
    def repotag(self):
        return self._repotag

    @property
    def manifest(self):
        return self._manifest

    @property
    def id(self):
        return self._id

    @property
    def repotags(self):
        return self._repotags

    @property
    def config(self):
        return self._config

    @property
    def layers(self):
        return self._layers

    @property
    def history(self):
        return self._history

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
        '''Load image metadata
        Currently there is no standard way to do this. For a specific tool,
        Inherit from this class and override this method'''
        pass
