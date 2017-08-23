import unittest

import utils.commands as cmds
import utils.metadata as md


class TestUtilCommands(unittest.TestCase):

    def setUp(self):
        cmds.docker_command(cmds.pull, True, 'debian:jessie')
        cmds.extract_image_metadata('debian:jessie')

    def testImageMetadata(self):
        self.assertTrue(md.get_image_manifest())

    def tearDown(self):
        md.clean_temp()


if __name__ == '__main__':
    unittest.main()
