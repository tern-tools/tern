# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest
from unittest.mock import Mock
import re

from tern.analyze import common
from test_fixtures import TestImage
from tern.classes.command import Command
from tern.utils import cache


class TestAnalyzeCommon(unittest.TestCase):

    def setUp(self):
        self.command1 = Command("yum install nfs-utils")
        self.image = TestImage('5678efgh')
        cache.cache = {}
        self.test_dockerfile = 'tests/dockerfiles/buildpack_deps_jessie_curl'

    def tearDown(self):
        del self.image
        del self.command1
        cache.cache = {}
        del self.test_dockerfile

    def testGetShellCommands(self):
        command, _ = common.get_shell_commands("yum install nfs-utils")
        self.assertEqual(type(command), list)
        self.assertEqual(len(command), 1)
        self.assertEqual(command[0].options, self.command1.options)
        # test on branching command
        branching_script = "if [ -z $var ]; then yum install nfs-utils; fi"
        branch_command, report = common.get_shell_commands(branching_script)
        self.assertEqual(type(branch_command), list)
        # we will ignore branching command, so len should be 0
        self.assertEqual(len(branch_command), 0)
        # and the report should not be None
        self.assertTrue(report)

    def testLoadFromCache(self):
        '''Given a layer object, populate the given layer in case the cache
        isn't empty'''
        self.image.load_image()
        # No cache
        self.assertFalse(common.load_from_cache(
            self.image.layers[0], redo=True))

        # Cache populated
        layer = self.image.layers[0]
        cache.cache = {
            layer.fs_hash: {
                'files_analyzed': False,
                'os_guess': 'Ubuntu',
                'pkg_format': 'tar',
                'files': [{'name': 'README.md',
                           'path': '/home/test/projectsX'}],
                'extension_info': {},
                'packages': [{'name': 'README'}]
            }}
        self.assertTrue(common.load_from_cache(
            self.image.layers[0], redo=False))

    def testLoadFilesFromCache(self):
        '''Given a layer object, populate the files of given layer in case
        the cache isn't empty'''
        self.image.load_image()

        # not loaded in cache
        layer = self.image.layers[0]
        layer.add_files = Mock(return_value=None)
        self.assertFalse(common.load_files_from_cache(layer))

        # Empty files
        layer = self.image.layers[0]
        cache.cache = {
            layer.fs_hash: {
                'files_analyzed': False,
                'files': [],
                'packages': [{'name': 'README.md',
                              'path': '/home/test/projectsX'}]
            }}
        layer.add_files = Mock(return_value=None)
        self.assertFalse(common.load_files_from_cache(layer))

        # With no empty files
        layer.add_files = Mock(return_value=None)
        cache.cache[layer.fs_hash]['files'].append(
            {'name': 'README.md',
             'path': '/home/test/projectsX',
             'origins': [{'origin_str': 'security issue',
                          'notices': [{
                              'message': 'Missing security policy',
                              'level': 'info'}]}
                         ]})

        self.assertEqual(common.load_files_from_cache(layer), None)
        self.assertFalse(layer.add_files.called)

    def testLoadPackagesFromCache(self):
        '''Given a layer object, populate the packages of given layer in case
        the cache isn't empty'''
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
        cache.cache[layer.fs_hash]['packages'].append(
            {'name': 'README.md',
             'origins': [{
                 'origin_str': 'security issue',
                 'notices': [{
                     'message': 'Missing security policy',
                     'level': 'info'}]}
             ]})

        self.assertTrue(common.load_packages_from_cache(layer))
        self.assertTrue(layer.add_package.called)

    def testLoadNoticesFromCache(self):
        '''Given a layer object, populate the notices messages of given
        layer in case the cache isn't empty'''
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

    def testGetGitURL(self):
        ''' we check the url to be the following form:
        github.com/<username>/tern'''
        url_list = common.get_git_url(self.test_dockerfile)
        check_num = len(url_list)
        pass_num = 0
        git_username_reg = r'([a-zA-Z\d_-]{0,38})'
        pattern = re.compile(r'github.com/'+git_username_reg+r'/tern')
        for url in url_list:
            if pattern.match(url):
                pass_num += 1
        self.assertEqual(pass_num, check_num)


if __name__ == '__main__':
    unittest.main()
