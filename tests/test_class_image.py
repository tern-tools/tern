'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest
import subprocess

from classes.image import Image
from utils.container import docker_command
from utils.container import pull


class TestClassImage(unittest.TestCase):

    def setUp(self):
        '''Using a specific image here. If this test fails due to the image
        not being found anymore, pick a different image to test against
        For now use Docker to pull the image from Dockerhub'''
        try:
            docker_command(pull, 'vmware/photon:1.0')
        except subprocess.CalledProcessError as error:
            print(error.output)
        self.image = Image('vmware/photon:1.0')
        # constants for this image
        self.id = ('25ebfa5ab0b7aee41b2d4fbdc675a39b13c4a5d69bd5c80a25674b8c18'
                   '24cbe1')
        self.layer = ('00ab136ba3d1354c7ed46f67af6a7b3fbc849bcce56fee20c0bcf7d'
                      'b7e22f971')
        self.no_layers = 1

    def tearDown(self):
        del self.image

    def testInstance(self):
        self.assertEqual(self.image.repotag, 'vmware/photon:1.0')
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


if __name__ == '__main__':
    unittest.main()
