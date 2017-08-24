import unittest

import utils.commands as cmds
import utils.metadata as md


class TestUtilCommands(unittest.TestCase):

    def setUp(self):
        cmds.docker_command(cmds.pull, True, 'debian:jessie')
        cmds.extract_image_metadata('debian:jessie')

    def testImageMetadata(self):
        manifest = md.get_image_manifest()
        self.assertTrue(manifest)
        layers = md.get_image_layers(manifest)
        self.assertEqual(len(layers), 1)

    def tearDown(self):
        cmds.remove_image('debian:jessie')
        md.clean_temp()


if __name__ == '__main__':
    unittest.main()
