'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import unittest

import utils.commands as cmds
import utils.metadata as md


class TestUtilCommands(unittest.TestCase):

    def setUp(self):
        cmds.docker_command(cmds.pull, 'debian:jessie')

    def testImageMetadata(self):
        self.assertTrue(cmds.extract_image_metadata('debian:jessie'))
        self.assertFalse(cmds.extract_image_metadata('repo:tag'))

    def tearDown(self):
        cmds.remove_image('debian:jessie')
        md.clean_temp()


if __name__ == '__main__':
    unittest.main()
