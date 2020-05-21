# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest
import subprocess  # nosec

from tern.__main__ import create_top_dir
from tern.analyze.docker import container
from tern.analyze.docker.container import check_image, check_docker_setup
from tern.classes.docker_image import DockerImage
from tern.utils.rootfs import set_mount_dir


class TestClassDockerImage(unittest.TestCase):

    def setUp(self):
        '''Using a specific image here. If this test fails due to the image
        not being found anymore, pick a different image to test against
        For now use Docker to pull the image from Dockerhub'''
        set_mount_dir()
        create_top_dir()
        check_docker_setup()
        if not check_image('vmware/tern@sha256:20b32a9a20752aa1ad'
                           '7582c667704fda9f004cc4bfd8601fac7f2656c7567bb4'):
            try:
                container.pull_image('vmware/tern@sha256:20b32a9a20'
                                     '752aa1ad7582c667704fda9f004cc4'
                                     'bfd8601fac7f2656c7567bb4')
            except subprocess.CalledProcessError as error:
                print(error.output)
        self.image = DockerImage('vmware/tern@sha256:20b32'
                                 'a9a20752aa1ad7582c667704fda9f00'
                                 '4cc4bfd8601fac7f2656c7567bb4')
        # constants for this image
        self.image_id = ('acb194ad84d0f9734e794fbbdbb65fb'
                         '7db6eda83f33e9e817bcc75b1bdd99f5e')
        self.layer = ('c1c3a87012e7ff5791b31e94515b661'
                      'cdf06f6d5dc2f9a6245eda8774d257a13')
        self.no_layers = 1
        self.created_by = ('/bin/sh -c #(nop) ADD '
                           'file:92137e724f46c720d8083a11290c67'
                           'd9daa387e523336b1757a0e3c4f5867cd5 '
                           'in / ')
        self.file_info = [
            ('file2.txt', 'documents/test/file2.txt',
             '9710f003d924890c7677b4dd91fd753f6ed71cc57d4f'
             '9482261b6786d81957fa',
             'sha256'),
            ('file2.txt', 'documents/test/test2/file2.txt',
             '885000512dee8ac814641bbf6a7c887012ec23a2fb3e'
             '3b2cff583c45a611317d',
             'sha256'),
            ('file1.txt', 'documents/test/test2/file1.txt',
             '885000512dee8ac814641bbf6a7c887012ec'
             '23a2fb3e3b2cff583c45a611317d',
             'sha256'),
            ('file1.txt', 'documents/test/file1.txt',
             'a3cccbc52486d50a86ff0bc1e6ea0e0b701ac'
             '4bb139f8713fa136ef9ec68e97e',
             'sha256')
        ]

    def tearDown(self):
        container.close_client()
        del self.image

    def testInstance(self):
        self.assertEqual(self.image.repotag, 'vmware/tern@sha256:20b32a9a2'
                                             '0752aa1ad7582c667704fda9f004cc4'
                                             'bfd8601fac7f2656c7567bb4')
        self.assertEqual(self.image.name, 'vmware/tern')
        self.assertEqual(self.image.tag, '')
        self.assertTrue(self.image.checksum_type, 'sha256')
        self.assertTrue(self.image.checksum, '20b32a9a20752aa1ad7582c66'
                                             '7704fda9f004cc4bfd8601fac7'
                                             'f2656c7567bb4')
        self.assertFalse(self.image.image_id)
        self.assertFalse(self.image.manifest)
        self.assertFalse(self.image.repotags)
        self.assertFalse(self.image.config)
        self.assertFalse(self.image.layers)
        self.assertFalse(self.image.history)
        # test instantiating with a tag
        if not check_image('vmware/tern:testimage'):
            try:
                container.pull_image('vmware/tern:testimage')
            except subprocess.CalledProcessError as error:
                print(error.output)

        d = DockerImage('vmware/tern:testimage')
        self.assertEqual(d.name, 'vmware/tern')
        self.assertEqual(d.tag, 'testimage')
        self.assertEqual(d.checksum_type, 'sha256')
        self.assertEqual(d.checksum, '20b32a9a20752aa1ad7582c667704fda9f004cc4'
                                     'bfd8601fac7f2656c7567bb4')

    def testLoadImage(self):
        self.image.load_image()
        self.assertEqual(self.image.image_id, self.image_id)
        self.assertEqual(self.image.layers[0].diff_id, self.layer)
        self.assertEqual(len(self.image.layers), self.no_layers)
        self.assertEqual(self.image.layers[0].created_by, self.created_by)
        self.assertEqual(self.image.layers[0].checksum_type, 'sha256')
        self.assertEqual(self.image.layers[0].checksum, self.layer)

    def testGetImageOption(self):
        self.assertEqual(self.image.get_image_option(), self.image.repotag)

    def testGetLayerDiffIds(self):
        self.image.load_image()
        self.assertEqual(len(self.image.get_layer_diff_ids()), self.no_layers)
        self.assertEqual(self.image.get_layer_diff_ids()[0], self.layer)

    def testLayerFiles(self):
        self.image.load_image()
        self.assertFalse(self.image.layers[0].files)
        self.image.layers[0].add_files()
        for file in self.image.layers[0].files:
            self.assertTrue(
                (file.name, file.path, file.checksum,
                 file.checksum_type) in
                self.file_info
            )


if __name__ == '__main__':
    unittest.main()
