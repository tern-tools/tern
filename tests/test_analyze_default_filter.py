# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.analyze.default import filter as fltr
from tern.classes.command import Command


class TestAnalyzeDefaultFilter(unittest.TestCase):

    def setUp(self):
        self.command1 = Command("yum install nfs-utils")
        self.command2 = Command("yum remove nfs-utils")

    def tearDown(self):
        del self.command1
        del self.command2

    def testFilterInstallCommands(self):
        commands, _ = fltr.filter_install_commands("yum install")
        self.assertEqual(len(commands), 1)
        commands, _ = fltr.filter_install_commands("yum remove")
        self.assertEqual(len(commands), 1)

        # Negative Scenarios
        commands, _ = fltr.filter_install_commands("yum clean")
        self.assertEqual(len(commands), 0)
        commands, _ = fltr.filter_install_commands("yum")
        self.assertEqual(len(commands), 0)

    def testConsolidateCommandsWithDifferentCommands(self):
        commands_list = fltr.consolidate_commands(
            [self.command1, self.command2])
        self.assertEqual(len(commands_list), 1)
        self.assertEqual(len(commands_list[0].words), 3)

    def testConsolidateCommandsWithSameCommands(self):
        command = Command("yum install nfs-utils")
        commands_list = fltr.consolidate_commands([self.command1, command])
        self.assertEqual(len(commands_list), 1)
        self.assertEqual(len(commands_list[0].words), 2)

        command = Command("yum remove nfs-utils")
        commands_list = fltr.consolidate_commands([self.command2, command])
        self.assertEqual(len(commands_list), 1)
        self.assertEqual(len(commands_list[0].words), 2)

    def testRemoveIgnoredCommandsWithIgnoreFlag(self):
        self.command1.set_ignore()
        _, c = fltr.remove_ignored_commands([self.command1])
        self.assertEqual(len(c), 0)

    def testRemoveIgnoredCommandsWithoutIgnoreFlag(self):
        # Negative Scenarios
        _, c = fltr.remove_ignored_commands([self.command1])
        self.assertEqual(len(c), 1)

    def testRemoveUnrecognizedCommandsWithoutFlag(self):
        _, c = fltr.remove_unrecognized_commands([self.command1])
        self.assertEqual(len(c), 0)

    def testRemoveUnrecognizedCommandsWithFlag(self):
        # Negative Scenarios
        self.command1.set_install()
        _, c = fltr.remove_unrecognized_commands([self.command1])
        self.assertEqual(len(c), 1)

    def testGetInstalledPackageNamesWithInstallFlag(self):
        self.command1.set_install()
        self.assertGreater(
            len(fltr.get_installed_package_names(self.command1)), 0)

    def testGetInstalledPackageNamesWithRemoveFlag(self):
        # Negative Scenarios
        self.command2.set_remove()
        self.assertEqual(
            len(fltr.get_installed_package_names(self.command2)), 0)


if __name__ == '__main__':
    unittest.main()
