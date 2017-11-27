'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
'''

import unittest

from classes.layer import Layer
from classes.package import Package


class TestClassLayer(unittest.TestCase):

    def setUp(self):
        self.layer = Layer('123abc')

    def tearDown(self):
        del self.layer

    def testInstance(self):
        self.assertEqual(self.layer.sha, '123abc')
        self.assertFalse(self.layer.packages)
        self.assertRaises(AttributeError, setattr, self.layer, 'sha', '456def')

    def testAddingPackage(self):
        p1 = Package('x')
        self.layer.add(p1)
        self.assertEqual(len(self.layer.packages), 1)

    def testRemovePackage(self):
        p1 = Package('x')
        p2 = Package('y')
        self.layer.add(p1)
        self.layer.add(p2)
        self.assertTrue(self.layer.remove('y'))
        self.assertFalse(self.layer.remove('y'))

    def testToDict(self):
        p1 = Package('x')
        self.layer.add(p1)
        a_dict = self.layer.to_dict()
        print(a_dict)
        self.assertTrue(a_dict['123abc'])
        self.assertEqual(len(a_dict['123abc']), 1)
        self.assertEqual(a_dict['123abc'][0]['name'], 'x')


if __name__ == '__main__':
    unittest.main()
