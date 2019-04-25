# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import unittest

from tern.classes.image import Image
from tern.classes.origins import Origins
from test_fixtures import TestImage
from test_fixtures import TestTemplate1
from test_fixtures import TestTemplate2


class TestClassImage(unittest.TestCase):

    def setUp(self):
        '''Test a generic Image class'''
        self.image1 = Image('1234abcd')
        self.image2 = TestImage('5678efgh')

    def tearDown(self):
        del self.image1
        del self.image2

    def testInstance(self):
        self.assertEqual(self.image1.image_id, '1234abcd')
        self.assertFalse(self.image1.name)
        self.assertFalse(self.image1.manifest)
        self.assertFalse(self.image1.tag)
        self.assertFalse(self.image1.config)
        self.assertFalse(self.image1.layers)
        self.assertIsInstance(self.image1.origins, Origins)

    def testLoadImage(self):
        self.assertEqual(self.image2.image_id, '5678efgh')
        self.assertFalse(self.image2.layers)
        self.image2.load_image()
        self.assertEqual(len(self.image2.layers), 1)
        self.assertEqual(len(self.image2.layers[0].packages), 2)

    def testGetLayerDiffIds(self):
        self.image2.load_image()
        self.assertEqual(self.image2.get_layer_diff_ids(), ['123abc'])

    def testGetLayerObject(self):
        self.image2.load_image()
        self.assertEqual(
             self.image2.get_layer_object('123abc'), self.image2.layers[0])

    def testToDict(self):
        self.image2.load_image()
        a_dict = self.image2.to_dict()
        self.assertEqual(a_dict['image_id'], '5678efgh')
        self.assertEqual(len(a_dict['layers']), 1)
        self.assertEqual(len(a_dict['layers'][0]['packages']), 2)

    def testToDictTemplate(self):
        self.image2.load_image()
        template1 = TestTemplate1()
        template2 = TestTemplate2()
        dict1 = self.image2.to_dict(template1)
        dict2 = self.image2.to_dict(template2)
        self.assertEqual(len(dict1.keys()), 2)
        self.assertEqual(dict1['image.id'], '5678efgh')
        self.assertEqual(len(dict1['image.layers']), 1)
        self.assertEqual(len(dict2.keys()), 3)
        self.assertFalse(dict2['notes'])
        self.assertFalse(dict2['image.layers'][0]['notes'])
        self.assertEqual(len(dict2['image.layers'][0]['layer.packages']), 2)


if __name__ == '__main__':
    unittest.main()
