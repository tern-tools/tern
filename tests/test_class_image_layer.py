'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest

from classes.image_layer import ImageLayer
from classes.package import Package


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
        p1 = Package('x')
        self.layer.add_package(p1)
        self.assertEqual(len(self.layer.packages), 1)

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
        self.assertTrue(a_dict['123abc'])
        self.assertEqual(len(a_dict['123abc']['packages']), 1)
        self.assertEqual(a_dict['123abc']['packages'][0]['name'], 'x')
        self.assertEqual(a_dict['123abc']['tar_file'], 'path/to/tar')

    def testGetPackageNames(self):
        p1 = Package('x')
        self.layer.add_package(p1)
        pkgs = self.layer.get_package_names()
        self.assertEqual(pkgs[0], 'x')


if __name__ == '__main__':
    unittest.main()
