# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.load import docker_api
from tern.utils import rootfs
from test_fixtures import create_working_dir
from test_fixtures import remove_working_dir


class TestLoadDockerAPI(unittest.TestCase):
    """This test case requires a temporary folder to be set up and the Docker
    daemon to be up and running properly"""

    def setUp(self):
        self.client = docker_api.check_docker_setup()
        create_working_dir()
        rootfs.set_working_dir()

    def tearDown(self):
        # should not do anything if the client is already closed
        docker_api.close_client(self.client)
        # clean up working directory
        remove_working_dir()

    def testBuildAndRemoveImage(self):
        # working dockerfile
        dockerfile_path = 'tests/dockerfiles/debian_buster_apt'
        image_obj = docker_api.build_image(dockerfile_path, self.client)
        self.assertTrue(image_obj)
        # successful remove
        self.assertTrue(docker_api.remove_image(image_obj, self.client))
        # remove an image that is not there
        self.assertFalse(docker_api.remove_image(image_obj, self.client))
        # no dockerfile
        image_obj = docker_api.build_image(
            'dockerfiles/not_there', self.client)
        self.assertFalse(image_obj)
        # failed build
        image_obj = docker_api.build_image(
            'tests/dockerfiles/fail_build', self.client)
        self.assertFalse(image_obj)

    def testExtractImage(self):
        # successful save
        dockerfile_path = 'tests/dockerfiles/debian_buster_apt'
        image_obj = docker_api.build_image(dockerfile_path, self.client)
        self.assertTrue(docker_api.extract_image(image_obj))
        docker_api.remove_image(image_obj, self.client)


if __name__ == '__main__':
    unittest.main()
