# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.load import skopeo
from tern.classes.oci_image import OCIImage
from tern.utils import rootfs
from test_fixtures import create_working_dir
from test_fixtures import remove_working_dir


class TestClassOCIImage(unittest.TestCase):

    def setUp(self):
        '''Using a specific image here. If this test fails due to the image
        not being found anymore, pick a different image to test against
        For now use Docker to pull the image from Dockerhub'''
        create_working_dir()
        rootfs.set_working_dir()
        # this should check if the docker image extraction is successful
        skopeo.pull_image('vmware/tern@sha256:20b32a9a20752aa1ad7582c667704f'
                          'da9f004cc4bfd8601fac7f2656c7567bb4')
        self.image = OCIImage('vmware/tern@sha256:20b32a9a20752aa1ad7582c6'
                              '67704fda9f004cc4bfd8601fac7f2656c7567bb4')
        # constants for this image
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
        del self.image
        remove_working_dir()

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
        self.assertFalse(self.image.manifest)
        self.assertFalse(self.image.config)
        self.assertFalse(self.image.layers)
        self.assertFalse(self.image.history)
        # test instantiating with a tag
        o = OCIImage('vmware/tern:testimage')
        self.assertEqual(o.name, 'vmware/tern')
        self.assertEqual(o.tag, 'testimage')
        self.assertFalse(o.checksum_type)
        self.assertFalse(o.checksum)

    def testLoadImage(self):
        self.image.load_image()
        self.assertEqual(self.image.layers[0].diff_id, self.layer)
        self.assertEqual(len(self.image.layers), self.no_layers)
        self.assertEqual(self.image.layers[0].created_by, self.created_by)
        self.assertEqual(self.image.layers[0].checksum_type, 'sha256')
        self.assertEqual(self.image.layers[0].checksum, self.layer)

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
