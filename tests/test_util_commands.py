import unittest

import utils.commands as cmds


class TestUtilMetadata(unittest.TestCase):

    def setUp(self):
        cmds.docker_command(cmds.pull, True, 'debian:jessie')

    def testDockerCommand(self):
        self.assertTrue(cmds.extract_image_metadata('debian:jessie'))
        self.assertFalse(cmds.extract_image_metadata('repo:tag'))

    def tearDown(self):
        cmds.remove_image('debian:jessie')
        cmds.clean_temp()


if __name__ == '__main__':
    unittest.main()
