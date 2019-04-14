# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import unittest

import utils.commands
import utils.metadata


class TestUtilCommands(unittest.TestCase):

    def setUp(self):
        utils.commands.docker_command(utils.commands.pull, 'debian:jessie')
        utils.commands.extract_image_metadata('debian:jessie')

    def testImageMetadata(self):
        manifest = utils.metadata.get_image_manifest()
        self.assertTrue(manifest)
        layers = utils.metadata.get_image_layers(manifest)
        self.assertEqual(len(layers), 1)

    def tearDown(self):
        utils.commands.remove_image('debian:jessie')
        utils.metadata.clean_temp()


if __name__ == '__main__':
    unittest.main()
