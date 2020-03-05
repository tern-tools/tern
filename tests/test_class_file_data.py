# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.classes.file_data import FileData
from test_fixtures import TestTemplate1
from test_fixtures import TestTemplate2


class TestClassFileData(unittest.TestCase):

    def setUp(self):
        self.afile = FileData('afile',
                              'path/to/afile')
        self.afile.licenses = ['MIT', 'GPL']

    def tearDown(self):
        del self.afile

    def testInstance(self):
        file1 = FileData('file1', 'path/to/file1')
        self.assertEqual(file1.name, 'file1')
        self.assertEqual(file1.path, 'path/to/file1')
        self.assertFalse(file1.checksum_type)
        self.assertFalse(file1.checksum)
        self.assertFalse(file1.date)
        self.assertFalse(file1.version_control)
        self.assertFalse(file1.version)
        self.assertFalse(file1.file_type)
        self.assertFalse(file1.licenses)
        self.assertFalse(file1.license_expressions)
        self.assertFalse(file1.copyrights)
        self.assertFalse(file1.authors)
        self.assertFalse(file1.packages)
        self.assertFalse(file1.urls)

        with self.assertRaises(ValueError):
            file2 = FileData('file2',
                             'path/to/file2',
                             '12355')
        file1.file_type = 'ELF'
        self.assertEqual(file1.file_type, 'ELF')
        file2 = FileData('file2',
                         'path/to/file2',
                         '2020-01-01',
                         'binary')
        self.assertEqual(file2.date, '2020-01-01')
        self.assertEqual(file2.file_type, 'binary')

        file2.licenses = ['MIT', 'GPL']
        file2.license_expressions = ['GPLv2 or MIT', 'MIT and GPLv2']
        file2.copyrights = ['copyrights']
        file2.authors = ['author1', 'author2']
        file2.packages = ['package1', 'package2']
        self.assertEqual(file2.licenses, ['MIT', 'GPL'])
        self.assertEqual(file2.license_expressions, ['GPLv2 or MIT',
                                                     'MIT and GPLv2'])
        self.assertEqual(file2.copyrights, ['copyrights'])
        self.assertEqual(file2.authors, ['author1', 'author2'])
        self.assertEqual(file2.packages, ['package1', 'package2'])

    def testSetChecksum(self):
        self.afile.set_checksum('sha256', '12345abcde')
        self.assertEqual(self.afile.checksum_type, 'sha256')
        self.assertEqual(self.afile.checksum, '12345abcde')

    def testExtAttrs(self):
        file = FileData('test.txt', 'usr/abc/test.txt')
        file.extattrs = '-rw-r--r--|1000|1000|19|1'
        self.assertEqual(file.extattrs, '-rw-r--r--|1000|1000|19|1')

    def testSetVersion(self):
        self.afile.set_version('git', '12345abcde')
        self.assertEqual(self.afile.version_control, 'git')
        self.assertEqual(self.afile.version, '12345abcde')

    def testToDict(self):
        file_dict = self.afile.to_dict()
        self.assertEqual(file_dict['name'], 'afile')
        self.assertEqual(file_dict['path'], 'path/to/afile')
        self.assertEqual(file_dict['licenses'], ['MIT', 'GPL'])

    def testToDictTemplate(self):
        template1 = TestTemplate1()
        template2 = TestTemplate2()
        dict1 = self.afile.to_dict(template1)
        dict2 = self.afile.to_dict(template2)
        self.assertEqual(len(dict1.keys()), 3)
        self.assertEqual(dict1['file.name'], 'afile')
        self.assertEqual(dict1['file.path'], 'path/to/afile')
        self.assertEqual(dict1['file.licenses'], ['MIT', 'GPL'])
        self.assertFalse(dict2['notes'])


if __name__ == '__main__':
    unittest.main()
