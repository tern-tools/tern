'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import unittest

from classes.package import Package


class TestClassPackage(unittest.TestCase):

    def setUp(self):
        self.package = Package('x')

    def tearDown(self):
        del self.package

    def testInstance(self):
        self.assertEqual(self.package.name, 'x')
        self.assertEqual(self.package.version, 0.0)
        self.assertFalse(self.package.src_url)
        self.assertFalse(self.package.license)

    def testSetters(self):
        self.assertRaises(AttributeError, setattr, self.package, 'name', 'y')
        self.package.version = 1.0
        self.assertEqual(self.package.version, 1.0)
        self.package.license = 'Apache 2.0'
        self.assertEqual(self.package.license, 'Apache 2.0')
        self.package.src_url = 'github.com'
        self.assertEqual(self.package.src_url, 'github.com')

    def testGetters(self):
        self.package.version = 1.0
        self.package.license = 'Apache 2.0'
        self.package.src_url = 'github.com'
        self.assertEqual(self.package.name, 'x')
        self.assertEqual(self.package.version, 1.0)
        self.assertEqual(self.package.license, 'Apache 2.0')
        self.assertEqual(self.package.src_url, 'github.com')

    def testToDict(self):
        self.package.version = 1.0
        self.package.license = 'Apache 2.0'
        self.package.src_url = 'github.com'
        a_dict = self.package.to_dict()
        self.assertEqual(a_dict['name'], 'x')
        self.assertEqual(a_dict['version'], 1.0)
        self.assertEqual(a_dict['license'], 'Apache 2.0')
        self.assertEqual(a_dict['src_url'], 'github.com')


if __name__ == '__main__':
    unittest.main()
