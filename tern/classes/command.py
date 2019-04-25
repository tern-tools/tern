# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

from tern.utils.general import parse_command


class Command:
    '''A representation of a shell command
    attributes:
        shell_command: the actual shell command
        name: command name (eg: apt-get)
        options: command options (-v or --verbose)
        words: a subcommand, arguments for the options or/and command arguments
        flags: a set of flags showing what kind of command it is
        This is a binary representation in this bit order:
            install remove ignore
        an install command is: 0b100 (4)
        a remove command is: 0b010 (2)
        to ignore this command: 0b001 (1)
    '''
    def __init__(self, shell_command):
        '''Use the shell command parser to populate the attributes'''
        self.__shell_command = shell_command
        command_dict = parse_command(self.__shell_command)
        self.__name = command_dict['name']
        self.__subcommand = ''
        self.__options = command_dict['options']
        self.__words = command_dict['words']
        self.__properties = ['subcommand', 'option_arg']
        self.__flags = 0b000
        self.__set_bit = 0b001

    @property
    def shell_command(self):
        return self.__shell_command

    @property
    def name(self):
        return self.__name

    @property
    def subcommand(self):
        return self.__subcommand

    @property
    def options(self):
        return self.__options

    @property
    def option_args(self):
        return self.__option_args

    @property
    def words(self):
        return self.__words

    @property
    def flags(self):
        return self.__flags

    def __set_prop(self, value, prop):
        if prop == 'subcommand':
            self.__subcommand = value
        if prop == 'option_arg':
            # Since the options and arguments are already listed
            # don't do anything
            pass

    def reassign_word(self, word, word_prop):
        '''Reassign a word from the list of words to the given property
        See self.__properties for the list of possible properties to
        reassign the word to. If the word or property does not exist
        return False'''
        if word not in self.__words:
            return False
        if word_prop not in self.__properties:
            return False
        the_word = self.__words.pop(self.__words.index(word))
        self.__set_prop(the_word, word_prop)
        return True

    def get_option_argument(self, option):
        '''Given an option flag, return the option argument. If there is
        no option with that name return None'''
        for opt in self.__options:
            if opt[0] == option:
                return opt[1]
        return None

    def is_set(self):
        '''Check if any flags are set'''
        return not(self.flags == 0b000)

    def set_install(self):
        '''Set install flag'''
        self.__flags = self.__set_bit << 2

    def set_remove(self):
        '''Set remove flag'''
        self.__flags = self.__set_bit << 1

    def set_ignore(self):
        '''Set ignore flag'''
        print(self.__set_bit)
        self.__flags = self.__set_bit

    def is_install(self):
        '''Is this an install command?'''
        return self.flags == 0b100

    def is_remove(self):
        '''Is this a remove command?'''
        return self.flags == 0b010

    def is_ignore(self):
        '''Is this a command to ignore?'''
        return self.flags == 0b001
