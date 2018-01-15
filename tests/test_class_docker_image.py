'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest
import subprocess

from classes.docker_image import DockerImage
from utils.container import docker_command
from utils.container import pull


class TestClassDockerImage(unittest.TestCase):

    def setUp(self):
        '''Using a specific image here. If this test fails due to the image
        not being found anymore, pick a different image to test against
        For now use Docker to pull the image from Dockerhub'''
        try:
            docker_command(pull, 'debian:jessie')
        except subprocess.CalledProcessError as error:
            print(error.output)
        self.image = DockerImage('debian:jessie')
        # constants for this image
        self.id = ('2fe79f06fa6d3fa9e877b4415fb189f89ca8a4ff4a954a3d84b2c84129'
                   '9cd127')
        self.layer = ('4bcdffd70da292293d059d2435c7056711fab2655f8b74f48ad0abe'
                      '042b63687')
        self.no_layers = 1

    def tearDown(self):
        del self.image

    def testInstance(self):
        self.assertEqual(self.image.repotag, 'debian:jessie')
        self.assertFalse(self.image.id)
        self.assertFalse(self.image.manifest)
        self.assertFalse(self.image.repotags)
        self.assertFalse(self.image.config)
        self.assertFalse(self.image.layers)
        self.assertFalse(self.image.history)

    def testLoadImage(self):
        self.image.load_image()
        self.assertEqual(self.image.id, self.id)
        self.assertEqual(self.image.layers[0].diff_id, self.layer)
        self.assertEqual(len(self.image.layers), self.no_layers)

    def testGetImageOption(self):
        self.assertEqual(self.image.get_image_option(), self.image.repotag)

    def testGetLayerDiffIds(self):
        self.image.load_image()
        self.assertEqual(len(self.image.get_layer_diff_ids()), self.no_layers)
        self.assertEqual(self.image.get_layer_diff_ids()[0], self.layer)


if __name__ == '__main__':
    unittest.main()
