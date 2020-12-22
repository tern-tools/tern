# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.classes.origins import Origins
from tern.utils.general import prop_names


class Image:
    '''A representation of the image to be analyzed
    attributes:
        repotag: The image's repository and tag or the repository and
        digest. However, in order to be compatible with any future image
        identification scheme, this can be any string.
        manifest: the json object representing the image manifest
        config: the image config metadata
        layers: list of loaded layer objects from the image
                (depends on --layer option)
        load_until_layer: image should be loaded up to this layer
        total_layers: total number of layers in image.
        checksum_type: the digest algorithm used to create the image checksum
        checksum: the checksum
        checksums: a list of tuples of the form (checksum_type, checksum)
    methods:
        load_image: this method is to be implemented in the derived classes
        get_layer_diff_ids: returns a list of layer diff ids only
        set_checksum: set the checksum of the image given the checksum type
        add_checksums: add new checksums in the existing list of the checksums
        to_dict: return a python dictionary representation of the image
    '''
    def __init__(self, repotag=None):
        '''Initialize using the image's repo name and tag string'''
        self._repotag = repotag
        self._name = ''
        self._tag = ''
        self._manifest = {}
        self._config = {}
        self._layers = []
        self._load_until_layer = 0
        self._total_layers = 0
        self._checksum_type = ''
        self._checksum = ''
        self._checksums = []
        self._origins = Origins()

    @property
    def manifest(self):
        return self._manifest

    @property
    def repotag(self):
        return self._repotag

    @property
    def config(self):
        return self._config

    @property
    def layers(self):
        return self._layers

    @property
    def load_until_layer(self):
        return self._load_until_layer

    @property
    def total_layers(self):
        return self._total_layers

    @property
    def origins(self):
        return self._origins

    @property
    def name(self):
        return self._name

    @property
    def checksum_type(self):
        return self._checksum_type

    @property
    def checksum(self):
        return self._checksum

    @property
    def checksums(self):
        return self._checksums

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, tag):
        self._tag = tag

    def set_checksum(self, checksum_type='', checksum=''):
        '''Set the checksum type and checksum of the image'''
        # TODO: calculate the checksum if not given
        self._checksum_type = checksum_type
        self._checksum = checksum

    def add_checksums(self, checksums):
        '''Add checksum tuples to checksums property'''
        for checksum in checksums:
            self._checksums.append(checksum)

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

    def load_image(self, load_until_layer=0):
        '''Load image metadata
        Currently there is no standard way to do this. For a specific tool,
        Inherit from this class and override this method'''

    def to_dict(self, template=None):
        '''Return a dictionary representation of the image'''
        # send template to layer's to_dict method
        layer_list = [layer.to_dict(template) for layer in self.layers]
        image_dict = {}
        if template:
            # use the template mapping for the key name
            for key, prop in prop_names(self):
                if prop in template.image().keys():
                    image_dict.update(
                        {template.image()[prop]: self.__dict__[key]})
            # update 'origins' and 'layers' values if mapping exists
            if 'origins' in template.image().keys():
                image_dict.update(
                    {template.image()['origins']: self.origins.to_dict()})
            if 'layers' in template.image().keys():
                image_dict.update({template.image()['layers']: layer_list})
        else:
            # use the property name
            for key, prop in prop_names(self):
                image_dict.update({prop: self.__dict__[key]})
            # update 'origins' and 'layers' lists
            image_dict.update({'layers': layer_list})
            image_dict.update({'origins': self.origins.to_dict()})
        return image_dict

    def get_human_readable_id(self):
        '''Some reports like SPDX want a unique name for the full image
        and this is currently not supported by any image tool. So using
        a combination of name and tag or name and checksum instead'''
        name = self.name
        if self.tag:
            name = name + '-{}'.format(self.tag)
        elif self.checksum:
            name = name + '-{}'.format(self.checksum)
        return name

    def get_download_location(self):
        '''Return the registry information from where the image came from.
        Currently, the image's metadata doesn't have this information'''
