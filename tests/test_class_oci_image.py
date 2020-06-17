# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import os
import shutil
import unittest
import subprocess  # nosec
from tern.utils import rootfs
from tern.report import report
from tern.utils import general
from tern.__main__ import create_top_dir
from tern.utils.rootfs import set_mount_dir
from tern.classes.oci_image import OCIImage


class TestClassOCIImage(unittest.TestCase):
    def setUp(self):
        '''Using a specific image here. It will pull a docker image
        and convert that into OCI format using `skopeo` utility.'''
        set_mount_dir()
        create_top_dir()
        oci_image_path = general.get_top_dir()
        self.image_name = "test"
        self.image_tag = "latest"
        oci_image = os.path.join(oci_image_path, self.image_name)
        image_string = "oci:{0}:{1}".format(oci_image, self.image_tag)
        try:
            if not os.path.exists(oci_image):
                cmd = ["skopeo", "copy", "docker://photon:3.0-20200626", image_string]
                rootfs.root_command(cmd)
        except subprocess.CalledProcessError as error:
            print(error.output)

        report.setup(image_tag_string=oci_image, image_type="oci")
        self.image = OCIImage(image_string)
        self.layer = (
            'c571a0f54bfedced3e82c91439f2b36f07d3f42ac3df20db88e242c100a6e3d6')
        self.no_layers = 1
        self.created_by = ('/bin/sh -c #(nop) ADD '
                           'file:a702523c66281e08513d982f9eb'
                           'abf71fefe0bfd756712719a10533d2ae71e37 in / ')

    def tearDown(self):
        del self.image

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(general.get_top_dir())

    def testInstance(self):
        self.assertEqual(self.image.name, self.image_name)
        self.assertEqual(self.image.tag, self.image_tag)
        self.assertFalse(self.image.manifest)
        self.assertFalse(self.image.config)
        self.assertFalse(self.image.layers)
        self.assertFalse(self.image.history)

    def testLoadImage(self):
        self.image.load_image()
        self.assertEqual(len(self.image.layers), self.no_layers)
        self.assertEqual(self.image.layers[0].created_by, self.created_by)
        self.assertEqual(self.image.layers[0].checksum_type, 'sha256')

    def testLayerFiles(self):
        self.image.load_image()
        self.assertFalse(self.image.layers[0].files)


if __name__ == '__main__':
    unittest.main()
