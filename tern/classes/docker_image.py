# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import json
import os
import subprocess  # nosec

from tern.utils import rootfs
from tern.utils import general
from tern.utils.constants import manifest_file
from tern.analyze.docker import container

from tern.classes.image_layer import ImageLayer
from tern.classes.image import Image


class DockerImage(Image):
    '''A representation of an image created by Docker
    See image.py for super class's attributes
    Docker Image specific attributes:
        repotags: the list of repotags associated with this image
        history: a list of commands used to create the filesystem layers
        to_dict: return a dict representation of the object
    '''
    def __init__(self, repotag=None, image_id=None):
        '''Initialize using repotag and image_id'''
        super().__init__(image_id)
        self.__repotag = repotag
        self.__repotags = []
        self.__history = None
        if self.repotag is not None:
            # parse the repotag
            repo_dict = general.parse_image_string(self.__repotag)
            self._name = repo_dict.get('name')
            self._tag = repo_dict.get('tag')
            self.set_checksum(
                repo_dict.get('digest_type'), repo_dict.get('digest'))
            if not self.checksum and general.check_tar(repotag) is False:
                # if there is no checksum, get the digest type
                docker_image = container.check_image(self.__repotag)
                # this object could be representing an image built from
                # a Dockerfile, so it may not have a digest
                # so check for that condition
                if docker_image.attrs['RepoDigests']:
                    image_name_digest = container.get_image_digest(
                        docker_image)
                    repo_dict = general.parse_image_string(image_name_digest)
                    self.set_checksum(
                        repo_dict.get('digest_type'), repo_dict.get('digest'))

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
        '''Return a dictionary representation of the Docker image'''
        # this should take care of 'origins' and 'layers'
        di_dict = super().to_dict(template)
        return di_dict

    def get_image_option(self):
        '''Check to see which value was used to init the image object
        Return the value that was used. If neither one was used raise
        NameError. If both were used return the id'''
        if self.repotag is not None and self.image_id is not None:
            return self.image_id
        if self.repotag is not None:
            return self.repotag
        if self.image_id is not None:
            return self.image_id
        raise NameError("Image object initialized with no repotag or ID")

    def get_image_manifest(self):
        '''Assuming that there is a temp folder with a manifest.json of
        an image inside, get a dict of the manifest.json file'''
        temp_path = rootfs.get_working_dir()
        with general.pushd(temp_path):
            with open(manifest_file) as f:
                json_obj = json.loads(f.read())
        return json_obj

    def get_image_layers(self, manifest):
        '''Given the manifest, return the layers'''
        layers = []
        for layer in manifest[0].get('Layers'):
            layers.append(layer)
        return layers

    def get_image_config_file(self, manifest):
        '''Given the manifest, return the config file'''
        return manifest[0].get('Config')

    def get_image_id(self, manifest):
        '''Given the manifest, return the image id
        This happens to be the config file's sha256sum'''
        config_file = self.get_image_config_file(manifest)
        return config_file.split('.')[0]

    def get_image_repotags(self, manifest):
        '''Given the manifest, return the list of image tag strings'''
        return manifest[0].get('RepoTags')

    def get_layer_sha(self, layer_path):
        '''Docker's layers are file paths starting with the ID.
        Get just the sha'''
        return os.path.dirname(layer_path)

    def get_image_config(self, manifest):
        '''Assuming there now exists a working directory where the image
        metadata exists, return the image config'''
        config_file = self.get_image_config_file(manifest)
        # assuming that the config file path is in the same root path as the
        # manifest file
        temp_path = rootfs.get_working_dir()
        with general.pushd(temp_path):
            with open(config_file) as f:
                json_obj = json.loads(f.read())
        return json_obj

    def get_image_history(self, config):
        '''If the config has the image history return it. Else return None'''
        if 'history' in config.keys():
            return config['history']
        return None

    def get_diff_ids(self, config):
        '''Given the image config, return the filesystem diff ids'''
        diff_ids = []
        for item in config['rootfs']['diff_ids']:
            diff_ids.append(item.split(':').pop())
        return diff_ids

    def get_diff_checksum_type(self, config):
        '''Get the checksum type that was used to calculate the diff_id
        of the image'''
        return config['rootfs']['diff_ids'][0].split(':')[0]

    def set_layer_created_by(self):
        '''Docker image history configuration consists of a list of commands
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
        '''Load image metadata using docker commands'''
        try:
            option = self.get_image_option()
            container.extract_image_metadata(option)
            self._manifest = self.get_image_manifest()
            self._image_id = self.get_image_id(self._manifest)
            self.__repotags = self.get_image_repotags(self._manifest)
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
