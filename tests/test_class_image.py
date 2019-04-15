'''
Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest

from tern.classes.image import Image
from tern.classes.origins import Origins


class TestClassImage(unittest.TestCase):

    def setUp(self):
        '''Test a generic Image class'''
        self.image = Image('1234abcd')

    def tearDown(self):
        del self.image

    def testInstance(self):
        self.assertEqual(self.image.image_id, '1234abcd')
        self.assertFalse(self.image.name)
        self.assertFalse(self.image.manifest)
        self.assertFalse(self.image.tag)
        self.assertFalse(self.image.config)
        self.assertFalse(self.image.layers)
        self.assertIsInstance(self.image.origins, Origins)


if __name__ == '__main__':
    unittest.main()
