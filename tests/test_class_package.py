'''
Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest

from tern.classes.package import Package


class TestClassPackage(unittest.TestCase):

    def setUp(self):
        self.package = Package('x')

    def tearDown(self):
        del self.package

    def testInstance(self):
        self.assertEqual(self.package.name, 'x')
        self.assertEqual(self.package.version, '')
        self.assertFalse(self.package.src_url)
        self.assertFalse(self.package.license)

    def testSetters(self):
        self.assertRaises(AttributeError, setattr, self.package, 'name', 'y')
        self.package.version = '1.0'
        self.assertEqual(self.package.version, '1.0')
        self.package.license = 'Apache 2.0'
        self.assertEqual(self.package.license, 'Apache 2.0')
        self.package.src_url = 'github.com'
        self.assertEqual(self.package.src_url, 'github.com')

    def testGetters(self):
        self.package.version = '1.0'
        self.package.license = 'Apache 2.0'
        self.package.src_url = 'github.com'
        self.assertEqual(self.package.name, 'x')
        self.assertEqual(self.package.version, '1.0')
        self.assertEqual(self.package.license, 'Apache 2.0')
        self.assertEqual(self.package.src_url, 'github.com')

    def testToDict(self):
        self.package.version = '1.0'
        self.package.license = 'Apache 2.0'
        self.package.src_url = 'github.com'
        a_dict = self.package.to_dict()
        self.assertEqual(a_dict['name'], 'x')
        self.assertEqual(a_dict['version'], '1.0')
        self.assertEqual(a_dict['license'], 'Apache 2.0')
        self.assertEqual(a_dict['src_url'], 'github.com')

    def testIsEqual(self):
        p = Package('x')
        p.license = 'TestLicense'
        p.version = '1.0'
        p.src_url = 'TestUrl'
        self.package.license = 'TestLicense'
        self.package.version = '2.0'
        self.package.src_url = 'TestUrl'
        self.assertFalse(self.package.is_equal(p))
        p.version = '2.0'
        self.assertTrue(self.package.is_equal(p))


if __name__ == '__main__':
    unittest.main()
