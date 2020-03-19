# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.classes.file_data import FileData
from tern.classes.notice import Notice
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
        self.assertFalse(file1.short_file_type)
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
        with self.assertRaises(ValueError):
            file1.short_file_type = 'SOMETHING'
        file1.short_file_type = 'BINARY'
        self.assertEqual(file1.short_file_type, 'BINARY')
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

    def testAddChecksums(self):
        file1 = FileData('file1', 'path/to/file1')
        file1.add_checksums([('SHA1', '12345abcde'),
                             ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')])
        self.assertEqual(file1.checksums,
                         [('SHA1', '12345abcde'),
                          ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')])

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

    def testFill(self):
        file_dict = {
            'name': 'zconf.h',
            'path': '/usr/include/zconf.h',
            'checksum_type': 'sha256',
            'checksum': '77304005ceb5f0d03ad4c37eb8386a10866e'
                        '4ceeb204f7c3b6599834c7319541',
            'extattrs': '-rw-r--r-- 1 1000 1000 16262 Nov 13 17:57'
                        ' /usr/include/zconf.h',
            'checksums': [('SHA1', '12345abcde'),
                          ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')]
        }
        f = FileData('zconf.h', '/usr/include/zconf.h')
        f.fill(file_dict)
        self.assertEqual(f.name, 'zconf.h')
        self.assertEqual(f.path, '/usr/include/zconf.h')
        self.assertEqual(f.checksum_type, 'sha256')
        self.assertEqual(f.checksum, '77304005ceb5f0d03ad4c37eb838'
                                     '6a10866e4ceeb204f7c3b6599834c7319541')
        self.assertEqual(f.extattrs, '-rw-r--r-- 1 1000 1000 '
                                     '16262 Nov 13 17:57 /usr/include/zconf.h')
        self.assertEqual(f.checksums,
                         [('SHA1', '12345abcde'),
                          ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')]
                         )
        self.assertEqual(f.origins.origins[0].notices[0].message,
                         'No metadata for key: date')
        self.assertEqual(f.origins.origins[0].notices[1].message,
                         'No metadata for key: file_type')
        self.assertEqual(f.origins.origins[0].notices[1].level, 'warning')
        self.assertEqual(f.origins.origins[0].notices[2].message,
                         'No metadata for key: short_file_type')

    def testMerge(self):
        file1 = FileData('switch_root', 'sbin/switch_root')
        file1.set_checksum('sha256', '123abc456def')
        file1.extattrs = '-rwxr-xr-x|1000|1000|14408|1'
        file2 = FileData('switch_root', 'sbin/switch_root')
        file2.checksums = [('SHA1', '12345abcde'),
                           ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')]
        file2.set_checksum('sha256', '123abc456def')
        file2.extattrs = '-rwxr-xr-x|1000|1000|14408|1'
        file2.date = '2012-02-02'
        file2.file_type = 'binary'
        file2.short_file_type = 'BINARY'
        file2.licenses = ['MIT', 'GPL']
        file2.license_expressions = ['MIT or GPL']
        file2.copyrights = ['copyrights']
        file2.authors = ['author1', 'author2']
        file2.packages = ['package1', 'package2']
        file2.urls = ['url1', 'url2']
        file2.origins.add_notice_to_origins(
            'scanning', Notice('something happened', 'error'))
        file3 = FileData('switch_root', 'sbin/switch_root')
        file3.set_checksum('sha1', '456def123abc')
        file4 = FileData('e2image', 'sbin/e2image')
        self.assertFalse(file1.merge(file4))
        self.assertTrue(file1.merge(file3))
        self.assertEqual(file1.checksum, '123abc456def')
        self.assertEqual(file1.extattrs, '-rwxr-xr-x|1000|1000|14408|1')
        self.assertFalse(file1.merge('astring'))
        self.assertTrue(file1.merge(file2))
        self.assertEqual(file1.checksums,
                         [('SHA1', '12345abcde'),
                          ('MD5', '1ff38cc592c4c5d0c8e3ca38be8f1eb1')])
        self.assertEqual(file1.date, '2012-02-02')
        self.assertEqual(file1.file_type, 'binary')
        self.assertEqual(file1.short_file_type, 'BINARY')
        self.assertEqual(file1.licenses, ['MIT', 'GPL'])
        self.assertEqual(file1.license_expressions, ['MIT or GPL'])
        self.assertEqual(file1.copyrights, ['copyrights'])
        self.assertEqual(file1.authors, ['author1', 'author2'])
        self.assertEqual(file1.packages, ['package1', 'package2'])
        self.assertEqual(file1.urls, ['url1', 'url2'])
        self.assertEqual(len(file1.origins.origins), 1)
        self.assertEqual(file1.origins.origins[0].origin_str, 'scanning')
        self.assertEqual(len(file1.origins.origins[0].notices), 1)
        self.assertEqual(
            file1.origins.origins[0].notices[0].message, 'something happened')


if __name__ == '__main__':
    unittest.main()
