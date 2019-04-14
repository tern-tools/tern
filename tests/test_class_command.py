# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
import unittest

from classes.command import Command


class TestClassCommand(unittest.TestCase):

    def setUp(self):
        self.install = Command('apt-get install -y git')
        self.untar = Command('tar -x -C file tarfile.tar')
        self.download = Command('wget url')
        self.remove = Command('apt-get purge git')

    def tearDown(self):
        del self.install
        del self.untar
        del self.download
        del self.remove

    def testInstance(self):
        self.assertEqual(self.install.shell_command, 'apt-get install -y git')
        self.assertEqual(self.install.name, 'apt-get')
        # at this point the parser don't know that install is a subcommand
        self.assertFalse(self.install.subcommand)
        self.assertEqual(len(self.install.options), 1)
        self.assertEqual(self.install.options[0][0], '-y')
        # git isn't an option argument but it should still be in the option
        # tuple as it comes after -y
        self.assertEqual(self.install.options[0][1], 'git')
        self.assertEqual(len(self.install.words), 2)
        self.assertEqual(self.install.words[0], 'install')
        self.assertEqual(self.install.words[1], 'git')
        self.assertEqual(self.install.flags, 0)
        self.assertFalse(self.install.is_set())

        self.assertEqual(self.untar.shell_command,
                         'tar -x -C file tarfile.tar')
        self.assertEqual(self.untar.name, 'tar')
        self.assertFalse(self.untar.subcommand)
        self.assertEqual(len(self.untar.options), 2)
        self.assertFalse(self.untar.options[0][1])
        self.assertEqual(self.untar.options[1][1], 'file')
        # there are 2 words - file and tarfile.tar
        self.assertEqual(len(self.untar.words), 2)
        self.assertEqual(self.untar.words[0], 'file')
        self.assertEqual(self.untar.words[1], 'tarfile.tar')
        self.assertEqual(self.untar.flags, 0)
        self.assertFalse(self.untar.is_set())

        self.assertEqual(self.download.name, 'wget')
        self.assertFalse(self.download.subcommand)
        self.assertFalse(self.download.options)
        self.assertEqual(len(self.download.words), 1)
        self.assertEqual(self.download.words[0], 'url')
        self.assertEqual(self.download.flags, 0)
        self.assertFalse(self.download.is_set())

    def testReassignWord(self):
        # install is a subcommand
        self.assertTrue(self.install.reassign_word('install', 'subcommand'))
        self.assertFalse(self.install.reassign_word('install', 'subcommand'))
        # 'file' is an option argument
        self.assertTrue(self.untar.reassign_word('file', 'option_arg'))
        self.assertFalse(self.untar.reassign_word('file', 'option_arg'))
        # wget has no subcommands
        self.assertFalse(self.download.reassign_word('safe', 'subcommand'))

    def testGetOptionArgument(self):
        # in the case of the install command -y has no options but if it
        # did it should return 'git'
        self.assertEqual(self.install.get_option_argument('-y'), 'git')
        # for the tar command '-C' has the argument 'file'
        self.assertEqual(self.untar.get_option_argument('-C'), 'file')
        # for the wget command there are no options so this should
        # return None
        self.assertEqual(self.download.get_option_argument('-f'), None)

    def testFlags(self):
        # move install subcommand, then set the flag, then check to
        # see if the command is an install command
        self.install.reassign_word('install', 'subcommand')
        self.install.set_install()
        self.assertTrue(self.install.is_set())
        self.assertTrue(self.install.is_install())

        # ignore wget
        self.download.set_ignore()
        self.assertTrue(self.download.is_set())
        self.assertTrue(self.download.is_ignore())

        # set apt-get purge as a remove command
        self.remove.set_remove()
        self.assertTrue(self.remove.is_set())
        self.assertTrue(self.remove.is_remove())


if __name__ == '__main__':
    unittest.main()
