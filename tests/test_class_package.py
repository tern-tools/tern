'''
Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest

from tern.classes.package import Package


class TestClassPackage(unittest.TestCase):

    def setUp(self):
        self.p1 = Package('p1')
        self.p1.version = '1.0'
        self.p1.license = 'Apache 2.0'
        self.p1.src_url = 'github.com'

        self.p2 = Package('p2')

    def tearDown(self):
        del self.p1
        del self.p2

    def testInstance(self):
        self.assertEqual(self.p2.name, 'p2')
        self.assertFalse(self.p2.version)
        self.assertFalse(self.p2.src_url)
        self.assertFalse(self.p2.license)

    def testSetters(self):
        self.assertRaises(AttributeError, setattr, self.p2, 'name', 'y')
        self.p2.version = '2.0'
        self.assertEqual(self.p2.version, '2.0')
        self.p2.license = 'Apache 2.0'
        self.assertEqual(self.p2.license, 'Apache 2.0')
        self.p2.src_url = 'github.com'
        self.assertEqual(self.p2.src_url, 'github.com')

    def testGetters(self):
        self.assertEqual(self.p1.name, 'p1')
        self.assertEqual(self.p1.version, '1.0')
        self.assertEqual(self.p1.license, 'Apache 2.0')
        self.assertEqual(self.p1.src_url, 'github.com')

    def testToDict(self):
        a_dict = self.p1.to_dict()
        self.assertEqual(a_dict['name'], 'p1')
        self.assertEqual(a_dict['version'], '1.0')
        self.assertEqual(a_dict['license'], 'Apache 2.0')
        self.assertEqual(a_dict['src_url'], 'github.com')
        self.assertFalse(a_dict['origins'])

    def testIsEqual(self):
        p = Package('p2')
        p.license = 'TestLicense'
        p.version = '1.0'
        p.src_url = 'TestUrl'
        self.p2.license = 'TestLicense'
        self.p2.version = '2.0'
        self.p2.src_url = 'TestUrl'
        self.assertFalse(self.p2.is_equal(p))
        p.version = '2.0'
        self.assertTrue(self.p2.is_equal(p))


if __name__ == '__main__':
    unittest.main()
