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

    def testImageMetadata(self):
        self.assertTrue(utils.commands.extract_image_metadata('debian:jessie'))
        self.assertFalse(utils.commands.extract_image_metadata('repo:tag'))

    def tearDown(self):
        utils.commands.remove_image('debian:jessie')
        utils.metadata.clean_temp()


if __name__ == '__main__':
    unittest.main()
