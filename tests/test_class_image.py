'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest

from classes.image import Image


class TestClassImage(unittest.TestCase):

    def setUp(self):
        '''Test a generic Image class'''
        self.image = Image('debian:jessie')

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


if __name__ == '__main__':
    unittest.main()
