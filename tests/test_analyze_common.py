# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from unittest.mock import Mock

from tern.analyze import common
from test_fixtures import TestImage
from tern.classes.command import Command
from tern.classes.file_data import FileData
from tern.utils import cache


class TestAnalyzeCommon(unittest.TestCase):

    def setUp(self):
        self.command1 = Command("yum install nfs-utils")
        self.command2 = Command("yum remove nfs-utils")
        self.image = TestImage('5678efgh')
        self.file = FileData('README.txt', '/home/test')
        cache.cache = {}

    def tearDown(self):
        del self.image
        del self.command1
        del self.command2
        cache.cache = {}

    def testGetShellCommands(self):
        command = common.get_shell_commands("yum install nfs-utils")
        self.assertEqual(type(command), list)
        self.assertEqual(len(command), 1)
        self.assertEqual(command[0].options, self.command1.options)

    def testLoadFromCache(self):
        '''Given a layer object, populate the given layer in case the cache isn't empty'''
        self.image.load_image()
        # No cache
        self.assertFalse(common.load_from_cache(self.image.layers[0], redo=True))

        # Cache populated
        layer = self.image.layers[0]
        cache.cache = {
            layer.fs_hash: {
                'files_analyzed': False,
                'os_guess': 'Ubuntu',
                'pkg_format': 'tar',
                'files': [{'name': 'README.md', 'path': '/home/test/projectsX'}],
                'packages': [{'name': 'README'}]
            }}
        self.assertTrue(common.load_from_cache(self.image.layers[0], redo=False))

    def testLoadFilesFromCache(self):
        '''Given a layer object, populate the files of given layer in case the cache isn't empty'''
        self.image.load_image()

        # not loaded in cache
        layer = self.image.layers[0]
        layer.add_files = Mock(return_value=None)
        self.assertFalse(common.load_files_from_cache(layer))
        self.assertTrue(layer.add_files.called)

        # Empty files
        layer = self.image.layers[0]
        cache.cache = {
            layer.fs_hash: {
                'files_analyzed': False,
                'files': [],
                'packages': [{'name': 'README.md', 'path': '/home/test/projectsX'}]
            }}
        layer.add_files = Mock(return_value=None)
        self.assertFalse(common.load_files_from_cache(layer))
        self.assertTrue(layer.add_files.called)

        # With no empty files
        layer.add_files = Mock(return_value=None)
        cache.cache[layer.fs_hash]['files'].append({'name': 'README.md', 'path': '/home/test/projectsX', 'origins': [
            {'origin_str': 'security issue', 'notices': [{
                'message': 'Missing security policy',
                'level': 'info'
            }]}
        ]})

        self.assertEqual(common.load_files_from_cache(layer), None)
        self.assertFalse(layer.add_files.called)

    def testLoadPackagesFromCache(self):
        '''Given a layer object, populate the packages of given layer in case the cache isn't empty'''
        self.image.load_image()

        # not loaded in cache
        layer = self.image.layers[0]
        layer.add_package = Mock(return_value=None)
        self.assertFalse(common.load_packages_from_cache(layer))
        self.assertFalse(layer.add_package.called)

        # Empty files
        layer = self.image.layers[0]
        cache.cache = {
            layer.fs_hash: {
                'files_analyzed': False,
                'files': [],
                'packages': []
            }}
        layer.add_package = Mock(return_value=None)
        self.assertFalse(common.load_packages_from_cache(layer))
        self.assertFalse(layer.add_package.called)

        # With no empty files
        layer.add_package = Mock(return_value=None)
        cache.cache[layer.fs_hash]['packages'].append({'name': 'README.md', 'origins': [
            {'origin_str': 'security issue', 'notices': [{
                'message': 'Missing security policy',
                'level': 'info'
            }]}
        ]})

        self.assertTrue(common.load_packages_from_cache(layer))
        self.assertTrue(layer.add_package.called)

    def testLoadNoticesFromCache(self):
        '''Given a layer object, populate the notices messages of given layer in case the cache isn't empty'''
        origin_str = 'security issue'

        self.image.load_image()

        # not loaded in cache
        layer = self.image.layers[0]
        cache.cache = {
            layer.fs_hash: {
                'origins': []
            }}
        layer.origins.add_notice_origin = Mock(return_value=None)
        layer.origins.add_notice_to_origins = Mock(return_value=None)
        common.load_notices_from_cache(layer)
        self.assertFalse(layer.origins.add_notice_origin.called)
        self.assertFalse(layer.origins.add_notice_to_origins.called)

        # With no empty
        layer.origins.add_notice_origin = Mock(return_value=None)
        layer.origins.add_notice_to_origins = Mock(return_value=None)
        cache.cache[layer.fs_hash]['origins'].append({
            'origin_str': origin_str, 'notices': [{
                'message': 'Missing security policy',
                'level': 'info'
            }]
        })
        common.load_notices_from_cache(layer)
        layer.origins.add_notice_origin.assert_called_with(origin_str)
        self.assertTrue(layer.origins.add_notice_to_origins.called)

    def testSaveToCache(self):
        '''Given a image object, check the image layers are cached'''
        self.image.load_image()
        layer = self.image.layers[0]
        cache.add_layer = Mock()

        common.save_to_cache(self.image)
        cache.add_layer.assert_called_once_with(layer)

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
