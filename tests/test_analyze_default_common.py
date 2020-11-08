# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.analyze.default import default_common as common
from test_fixtures import TestImage


class TestAnalyzeDefaultCommon(unittest.TestCase):

    def setUp(self):
        self.image = TestImage('5678efgh')

    def tearDown(self):
        del self.image

    def testUpdateMasterListWithoutPackages(self):
        self.image.load_image()
        layer = self.image.layers[0]
        master_list = list()
        common.update_master_list(master_list, layer)
        self.assertEqual(len(master_list), len(layer.packages))

    def testUpdateMasterListWithPackages(self):
        self.image.load_image()
        layer = self.image.layers[0]
        master_list = list()
        older_master_list = list()
        for pkg in layer.packages:
            master_list.append(pkg)
            older_master_list.append(pkg)

        common.update_master_list(master_list, layer)
        self.assertEqual(len(master_list), len(older_master_list))
        self.assertEqual(len(layer.packages), 0)

        for old_pkg in older_master_list:
            exists = False
            for pkg in master_list:
                if old_pkg.is_equal(pkg):
                    exists = True
                    break
            self.assertTrue(exists)


if __name__ == '__main__':
    unittest.main()
