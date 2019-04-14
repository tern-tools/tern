# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import unittest

from tern.classes.image_layer import ImageLayer
from tern.classes.package import Package
from test_fixtures import TestTemplate1
from test_fixtures import TestTemplate2


class TestClassImageLayer(unittest.TestCase):

    def setUp(self):
        self.layer = ImageLayer('123abc', 'path/to/tar')

    def tearDown(self):
        del self.layer

    def testInstance(self):
        self.assertEqual(self.layer.diff_id, '123abc')
        self.assertEqual(self.layer.tar_file, 'path/to/tar')
        self.assertFalse(self.layer.packages)
        self.assertFalse(self.layer.created_by)
        self.assertRaises(AttributeError, setattr, self.layer,
                          'diff_id', '456def')
        self.assertRaises(AttributeError, setattr, self.layer, 'tar_file',
                          'some/other/path')
        self.layer.created_by = 'some string'
        self.assertEqual(self.layer.created_by, 'some string')

    def testAddPackage(self):
        err = "Object type String, should be Package"
        p1 = Package('x')
        self.layer.add_package(p1)
        self.assertEqual(len(self.layer.packages), 1)
        with self.assertRaises(TypeError, msg=err):
            self.layer.add_package("not_a_package")

    def testRemovePackage(self):
        p1 = Package('x')
        p2 = Package('y')
        self.layer.add_package(p1)
        self.layer.add_package(p2)
        self.assertTrue(self.layer.remove_package('y'))
        self.assertFalse(self.layer.remove_package('y'))

    def testToDict(self):
        p1 = Package('x')
        self.layer.add_package(p1)
        a_dict = self.layer.to_dict()
        self.assertEqual(a_dict['diff_id'], '123abc')
        self.assertEqual(len(a_dict['packages']), 1)
        self.assertEqual(a_dict['packages'][0]['name'], 'x')
        self.assertEqual(a_dict['tar_file'], 'path/to/tar')

    def testToDictTemplate(self):
        template1 = TestTemplate1()
        template2 = TestTemplate2()
        p1 = Package('x')
        self.layer.add_package(p1)
        dict1 = self.layer.to_dict(template1)
        dict2 = self.layer.to_dict(template2)
        self.assertEqual(len(dict1.keys()), 3)
        self.assertEqual(dict1['layer.diff'], '123abc')
        self.assertEqual(dict1['layer.tarfile'], 'path/to/tar')
        self.assertEqual(len(dict1['layer.packages']), 1)
        self.assertEqual(len(dict2.keys()), 4)
        self.assertFalse(dict2['notes'])
        self.assertFalse(dict2['layer.packages'][0]['notes'])

    def testGetPackageNames(self):
        p1 = Package('x')
        self.layer.add_package(p1)
        pkgs = self.layer.get_package_names()
        self.assertEqual(pkgs[0], 'x')


if __name__ == '__main__':
    unittest.main()
