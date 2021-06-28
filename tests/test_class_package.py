# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.classes.file_data import FileData
from tern.classes.package import Package
from test_fixtures import TestTemplate1
from test_fixtures import TestTemplate2


class TestClassPackage(unittest.TestCase):

    def setUp(self):
        self.p1 = Package('p1')
        self.p1.version = '1.0'
        self.p1.pkg_license = 'Apache 2.0'
        self.p1.copyright = 'All Rights Reserved'
        self.p1.proj_url = 'github.com'
        self.p1.download_url = 'https://github.com'
        self.p1.checksum = '123abc456'
        self.p1.pkg_licenses = ['MIT', 'GPL']

        self.p2 = Package('p2')

    def tearDown(self):
        del self.p1
        del self.p2

    def testInstance(self):
        self.assertEqual(self.p2.name, 'p2')
        self.assertFalse(self.p2.version)
        self.assertFalse(self.p2.proj_url)
        self.assertFalse(self.p2.pkg_license)
        self.assertFalse(self.p2.copyright)
        self.assertFalse(self.p2.download_url)
        self.assertFalse(self.p2.checksum)
        self.assertFalse(self.p2.pkg_licenses)

    def testSetters(self):
        self.assertRaises(AttributeError, setattr, self.p2, 'name', 'y')
        self.p2.version = '2.0'
        self.assertEqual(self.p2.version, '2.0')
        self.p2.pkg_license = 'Apache 2.0'
        self.assertEqual(self.p2.pkg_license, 'Apache 2.0')
        self.p2.copyright = "All Rights Reserved"
        self.assertEqual(self.p2.copyright, 'All Rights Reserved')
        self.p2.proj_url = 'github.com'
        self.assertEqual(self.p2.proj_url, 'github.com')
        self.p2.download_url = 'https://github.com'
        self.assertEqual(self.p2.download_url, 'https://github.com')
        self.p2.checksum = '123abc456'
        self.assertEqual(self.p2.checksum, '123abc456')
        self.p2.pkg_licenses = ['license1', 'license2']
        self.assertEqual(self.p2.pkg_licenses, ['license1', 'license2'])
        self.p2.files = [FileData('a', '/usr/abc/a'),
                         FileData('b', '/usr/abc/b')]
        self.assertEqual((self.p2.files[0].name, self.p2.files[0].path),
                         ('a', '/usr/abc/a'))
        self.assertEqual((self.p2.files[1].name, self.p2.files[1].path),
                         ('b', '/usr/abc/b'))

    def testGetters(self):
        self.assertEqual(self.p1.name, 'p1')
        self.assertEqual(self.p1.version, '1.0')
        self.assertEqual(self.p1.pkg_license, 'Apache 2.0')
        self.assertEqual(self.p1.copyright, 'All Rights Reserved')
        self.assertEqual(self.p1.proj_url, 'github.com')
        self.assertEqual(self.p1.download_url, 'https://github.com')
        self.assertEqual(self.p1.checksum, '123abc456')
        self.assertEqual(self.p1.pkg_licenses, ['MIT', 'GPL'])

    def testAddFile(self):
        p1 = Package('package')
        f1 = FileData('test.java', 'abc/pqr/test.java')
        f2 = FileData('test.c', 'abc/pqr/test.c')
        p1.add_file(f1)
        p1.add_file(f2)
        self.assertEqual(len(p1.files), 2)
        with self.assertRaises(TypeError):
            p1.add_file('sample.cpp')

    def testRemoveFile(self):
        p1 = Package('package')
        f1 = FileData('test.java', 'abc/pqr/test.java')
        f2 = FileData('test.c', 'abc/pqr/test.c')
        p1.add_file(f1)
        p1.add_file(f2)
        self.assertTrue(p1.remove_file('abc/pqr/test.java'))
        self.assertEqual(len(p1.files), 1)
        self.assertTrue(p1.remove_file('abc/pqr/test.c'))
        self.assertEqual(len(p1.files), 0)
        self.assertFalse(p1.remove_file('abc'))

    def testGetFilePaths(self):
        p1 = Package('package')
        f1 = FileData('test.java', 'abc/pqr/test.java')
        f2 = FileData('test.c', 'abc/pqr/test.c')
        p1.add_file(f1)
        p1.add_file(f2)
        self.assertEqual(p1.get_file_paths(),
                         ['abc/pqr/test.java',
                          'abc/pqr/test.c'
                          ])

    def testToDict(self):
        f1 = FileData('test.java', 'abc/pqr/test.java')
        self.p1.add_file(f1)
        a_dict = self.p1.to_dict()
        self.assertEqual(a_dict['name'], 'p1')
        self.assertEqual(a_dict['version'], '1.0')
        self.assertEqual(a_dict['pkg_license'], 'Apache 2.0')
        self.assertEqual(a_dict['copyright'], 'All Rights Reserved')
        self.assertEqual(a_dict['proj_url'], 'github.com')
        self.assertEqual(a_dict['download_url'], 'https://github.com')
        self.assertFalse(a_dict['origins'])
        self.assertEqual(a_dict['checksum'], '123abc456')
        self.assertEqual(a_dict['files'][0]['name'], 'test.java')
        self.assertEqual(a_dict['files'][0]['path'], 'abc/pqr/test.java')
        self.assertEqual(a_dict['pkg_licenses'], ['MIT', 'GPL'])

    def testToDictTemplate(self):
        template1 = TestTemplate1()
        template2 = TestTemplate2()
        f1 = FileData('test.java', 'abc/pqr/test.java')
        self.p1.add_file(f1)
        dict1 = self.p1.to_dict(template1)
        dict2 = self.p1.to_dict(template2)
        self.assertEqual(len(dict1.keys()), 4)
        self.assertEqual(dict1['package.name'], 'p1')
        self.assertEqual(dict1['package.files'][0]['file.name'],
                         'test.java')
        self.assertEqual(dict1['package.version'], '1.0')
        self.assertEqual(dict1['package.license'], 'Apache 2.0')
        self.assertEqual(dict1['package.files'][0]['file.path'],
                         'abc/pqr/test.java')
        self.assertEqual(len(dict2.keys()), 6)
        self.assertFalse(dict2['notes'])

    def testIsEqual(self):
        p = Package('p2')
        p.pkg_license = 'Testpkg_license'
        p.version = '1.0'
        p.proj_url = 'TestUrl'
        p.checksum = 'abcdef'
        self.p2.pkg_license = 'Testpkg_license'
        self.p2.version = '2.0'
        self.p2.proj_url = 'TestUrl'
        self.p2.checksum = 'abcdef'
        self.assertFalse(self.p2.is_equal(p))
        p.version = '2.0'
        self.assertTrue(self.p2.is_equal(p))

    def testFill(self):
        p_dict = {'name': 'p1',
                  'version': '1.0',
                  'pkg_license': 'Apache 2.0',
                  'checksum': 'abcxyz',
                  'pkg_licenses': ['MIT', 'GPL'],
                  'files': [{'name': 'a.txt', 'path': '/usr/a.txt'},
                            {'name': 'b.txt', 'path': '/lib/b.txt'}],
                  'pkg_format': 'rpm'}
        p = Package('p1')
        p.fill(p_dict)
        self.assertEqual(p.name, 'p1')
        self.assertEqual(p.version, '1.0')
        self.assertEqual(p.pkg_license, 'Apache 2.0')
        self.assertEqual(p.checksum, 'abcxyz')
        self.assertEqual(p.pkg_licenses, ['MIT', 'GPL'])
        self.assertEqual(len(p.files), 2)
        self.assertEqual(p.files[0].name, 'a.txt')
        self.assertEqual(p.files[0].path, '/usr/a.txt')
        self.assertFalse(p.copyright)
        self.assertFalse(p.proj_url)
        self.assertEqual(len(p.origins.origins), 1)
        self.assertEqual(p.origins.origins[0].origin_str, 'p1')
        self.assertEqual(len(p.origins.origins[0].notices), 3)
        self.assertEqual(p.origins.origins[0].notices[0].message,
                         "No metadata for key: copyright")
        self.assertEqual(p.origins.origins[0].notices[0].level, 'warning')
        self.assertEqual(p.origins.origins[0].notices[1].message,
                         "No metadata for key: proj_url")
        self.assertEqual(p.origins.origins[0].notices[2].message,
                         "No metadata for key: download_url")

    def testMerge(self):
        p1 = Package('p1')
        p1.version = '1.0'
        p1.pkg_licenses = ['license1']
        p2 = Package('p1')
        p2.version = '1.0'
        p2.download_url = 'SomeUrl'
        p2.checksum = 'abc'
        p2.pkg_licenses = ['license2']
        self.assertFalse(p1.merge('astring'))
        self.assertTrue(p1.merge(p2))
        self.assertEqual(p1.download_url, 'SomeUrl')
        self.assertEqual(p1.checksum, 'abc')
        self.assertEqual(p1.pkg_licenses, ['license1', 'license2'])
        p2.version = '2.0'
        self.assertFalse(p1.merge(p2))


if __name__ == '__main__':
    unittest.main()
