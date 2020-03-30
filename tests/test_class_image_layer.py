# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.classes.image_layer import ImageLayer
from tern.classes.package import Package
from tern.classes.file_data import FileData
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
        self.layer.pkg_format = 'rpm'
        self.assertEqual(self.layer.pkg_format, 'rpm')
        self.layer.os_guess = 'operating system'
        self.assertEqual(self.layer.os_guess, 'operating system')
        self.assertFalse(self.layer.files_analyzed)
        self.layer.files_analyzed = True
        self.assertTrue(self.layer.files_analyzed)
        self.assertRaises(ValueError, setattr, self.layer,
                          'files_analyzed', 'some string')
        self.assertEqual("", self.layer.analyzed_output)
        self.layer.analyzed_output = 'some string'
        self.assertEqual(self.layer.analyzed_output, 'some string')
        self.assertRaises(ValueError, setattr, self.layer,
                          'analyzed_output', 123)

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

    def testAddFile(self):
        err = "Object type String, should be FileData"
        file1 = FileData('file1', 'path/to/file1')
        self.layer.add_file(file1)
        self.assertEqual(len(self.layer.files), 1)
        with self.assertRaises(TypeError, msg=err):
            self.layer.add_file("afile")

    def testRemoveFile(self):
        file1 = FileData('file1', 'path/to/file1')
        self.layer.add_file(file1)
        self.assertFalse(self.layer.remove_file('file1'))
        self.assertTrue(self.layer.remove_file('path/to/file1'))
        self.assertFalse(self.layer.remove_file('path/to/file1'))

    def testToDict(self):
        p1 = Package('x')
        f1 = FileData('file1', 'path/to/file1')
        self.layer.add_package(p1)
        self.layer.add_file(f1)
        a_dict = self.layer.to_dict()
        self.assertEqual(a_dict['diff_id'], '123abc')
        self.assertEqual(len(a_dict['packages']), 1)
        self.assertEqual(a_dict['packages'][0]['name'], 'x')
        self.assertEqual(len(a_dict['files']), 1)
        self.assertEqual(a_dict['files'][0]['name'], 'file1')
        self.assertEqual(a_dict['files'][0]['path'], 'path/to/file1')
        self.assertEqual(a_dict['tar_file'], 'path/to/tar')

    def testToDictTemplate(self):
        template1 = TestTemplate1()
        template2 = TestTemplate2()
        p1 = Package('x')
        self.layer.add_package(p1)
        f1 = FileData('file1', 'path/to/file1')
        self.layer.add_file(f1)
        dict1 = self.layer.to_dict(template1)
        dict2 = self.layer.to_dict(template2)
        self.assertEqual(len(dict1.keys()), 4)
        self.assertEqual(dict1['layer.diff'], '123abc')
        self.assertEqual(dict1['layer.tarfile'], 'path/to/tar')
        self.assertEqual(len(dict1['layer.packages']), 1)
        self.assertEqual(len(dict1['layer.files']), 1)
        self.assertEqual(len(dict2.keys()), 5)
        self.assertFalse(dict2['notes'])
        self.assertFalse(dict2['layer.packages'][0]['notes'])
        self.assertFalse(dict2['layer.files'][0]['notes'])

    def testGetPackageNames(self):
        p1 = Package('x')
        self.layer.add_package(p1)
        pkgs = self.layer.get_package_names()
        self.assertEqual(pkgs[0], 'x')

    def testGetFilePaths(self):
        f1 = FileData('file1', 'path/to/file1')
        f2 = FileData('file2', 'path/to/file2')
        self.layer.add_file(f1)
        self.layer.add_file(f2)
        file_paths = self.layer.get_file_paths()
        self.assertEqual(file_paths, ['path/to/file1', 'path/to/file2'])

    def testSetChecksum(self):
        self.layer.set_checksum('sha256', '12345abcde')
        self.assertEqual(self.layer.checksum_type, 'sha256')
        self.assertEqual(self.layer.checksum, '12345abcde')

    def testAddChecksums(self):
        self.layer.add_checksums([('SHA1', '12345abcde'),
                                  ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')])
        self.assertEqual(self.layer.checksums,
                         [('SHA1', '12345abcde'),
                          ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')])


if __name__ == '__main__':
    unittest.main()
