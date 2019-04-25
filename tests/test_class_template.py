# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import unittest

from test_fixtures import TestTemplate1
from test_fixtures import TestTemplate2


class TestClassTemplate(unittest.TestCase):
    '''Note that we cannot instantiate the abstract base class so we
    will use a test fixture which is a subclass of Template'''

    def setUp(self):
        self.template1 = TestTemplate1()
        self.template2 = TestTemplate2()

    def tearDown(self):
        del self.template1
        del self.template2

    def testPackage(self):
        mapping = self.template1.package()
        self.assertEqual(mapping['name'], 'package.name')
        self.assertEqual(mapping['version'], 'package.version')
        self.assertEqual(mapping['pkg_license'], 'package.pkg_license')

    def testImageLayer(self):
        mapping = self.template1.image_layer()
        self.assertEqual(mapping['diff_id'], 'layer.diff')
        self.assertEqual(mapping['tar_file'], 'layer.tarfile')
        self.assertEqual(mapping['packages'], 'layer.packages')

    def testImage(self):
        mapping = self.template1.image()
        self.assertEqual(mapping['image_id'], 'image.id')
        self.assertEqual(mapping['layers'], 'image.layers')

    def testNotice(self):
        mapping = self.template2.notice()
        self.assertEqual(mapping['level'], 'note.level')
        self.assertEqual(mapping['message'], 'note.message')

    def testNoticeOrigin(self):
        mapping = self.template2.notice_origin()
        self.assertEqual(mapping['origin_str'], 'note.source')
        self.assertEqual(mapping['notices'], 'note.messages')

    def testOrigins(self):
        mapping = self.template2.origins()
        self.assertEqual(mapping['origins'], 'notes')


if __name__ == '__main__':
    unittest.main()
