# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from tern.analyze import common
from test_fixtures import TestImage
from tern.classes.command import Command


class TestAnalyzeCommon(unittest.TestCase):

    def setUp(self):
        self.command1 = Command("yum install nfs-utils")
        self.command2 = Command("yum remove nfs-utils")
        self.image = TestImage('5678efgh')

    def tearDown(self):
        del self.image
        del self.command1
        del self.command2

    def testGetShellCommands(self):
        command = common.get_shell_commands("yum install nfs-utils")
        self.assertEqual(type(command), list)
        self.assertEqual(len(command), 1)
        self.assertEqual(command[0].options, self.command1.options)

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

    def testFilterInstallCommands(self):
        commands, _ = common.filter_install_commands("yum install")
        self.assertEqual(len(commands), 1)
        commands, _ = common.filter_install_commands("yum remove")
        self.assertEqual(len(commands), 1)

        # Negative Scenarios
        commands, _ = common.filter_install_commands("yum clean")
        self.assertEqual(len(commands), 0)
        commands, _ = common.filter_install_commands("yum")
        self.assertEqual(len(commands), 0)

    def testConsolidateCommandsWithDifferentCommands(self):
        commands_list = common.consolidate_commands(
            [self.command1, self.command2])
        self.assertEqual(len(commands_list), 1)
        self.assertEqual(len(commands_list[0].words), 3)

    def testConsolidateCommandsWithSameCommands(self):
        command = Command("yum install nfs-utils")
        commands_list = common.consolidate_commands([self.command1, command])
        self.assertEqual(len(commands_list), 1)
        self.assertEqual(len(commands_list[0].words), 2)

        command = Command("yum remove nfs-utils")
        commands_list = common.consolidate_commands([self.command2, command])
        self.assertEqual(len(commands_list), 1)
        self.assertEqual(len(commands_list[0].words), 2)

    def testRemoveIgnoredCommandsWithIgnoreFlag(self):
        self.command1.set_ignore()
        _, c = common.remove_ignored_commands([self.command1])
        self.assertEqual(len(c), 0)

    def testRemoveIgnoredCommandsWithoutIgnoreFlag(self):
        # Negative Scenarios
        _, c = common.remove_ignored_commands([self.command1])
        self.assertEqual(len(c), 1)

    def testRemoveUnrecognizedCommandsWithoutFlag(self):
        _, c = common.remove_unrecognized_commands([self.command1])
        self.assertEqual(len(c), 0)

    def testRemoveUnrecognizedCommandsWithFlag(self):
        # Negative Scenarios
        self.command1.set_install()
        _, c = common.remove_unrecognized_commands([self.command1])
        self.assertEqual(len(c), 1)

    def testGetInstalledPackageNamesWithInstallFlag(self):
        self.command1.set_install()
        self.assertGreater(
            len(common.get_installed_package_names(self.command1)), 0)

    def testGetInstalledPackageNamesWithRemoveFlag(self):
        # Negative Scenarios
        self.command2.set_remove()
        self.assertEqual(
            len(common.get_installed_package_names(self.command2)), 0)


if __name__ == '__main__':
    unittest.main()
