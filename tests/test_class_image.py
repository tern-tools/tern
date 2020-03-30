# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

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
        self.image3 = TestImage('f380a61e')

    def tearDown(self):
        del self.image1
        del self.image2
        del self.image3

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
        self.assertFalse(self.image2.name)
        self.assertFalse(self.image2.tag)
        self.image2.load_image()
        self.assertEqual(self.image2.name, 'testimage')
        self.assertEqual(self.image2.tag, 'testtag')
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

    def testGetHumanReadableId(self):
        self.assertEqual(self.image1.get_human_readable_id(), '1234abcd')
        self.image2.load_image()
        self.assertEqual(
            self.image2.get_human_readable_id(), '5678efgh-testimage-testtag')

    def testSetImageImport(self):
        self.image1.load_image()
        self.image2.load_image()
        self.image3.load_image()
        self.assertTrue(self.image3.set_image_import(self.image2))
        self.assertFalse(self.image3.set_image_import(self.image1))

    def testLastImportLayer(self):
        self.image1.load_image()
        self.image2.load_image()
        self.image3.load_image()
        self.image3.set_image_import(self.image1)
        self.assertTrue(self.image3.get_last_import_layer() is None)
        self.image3.set_image_import(self.image2)
        self.assertTrue(self.image3.get_last_import_layer() is not None)

    def testGetLastImportLayer(self):
        self.image2.load_image()
        self.assertTrue(self.image2.get_layer_object("123abc") is not None)
        self.assertTrue(self.image2.get_layer_object("1234abcd") is None)

    def testSetChecksum(self):
        self.image1.set_checksum('sha256', '12345abcde')
        self.assertEqual(self.image1.checksum_type, 'sha256')
        self.assertEqual(self.image1.checksum, '12345abcde')

    def testAddChecksums(self):
        self.image1.add_checksums([
            ('SHA1', '12345abcde'),
            ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')])
        self.assertEqual(self.image1.checksums,
                         [('SHA1', '12345abcde'),
                          ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')])


if __name__ == '__main__':
    unittest.main()
