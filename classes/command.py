'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''
from utils.general import parse_command


class Command(object):
    '''A representation of a shell command
    attributes:
        shell_command: the actual shell command
        name: command name (eg: apt-get)
        options: command options (-v or --verbose)
        words: a subcommand, arguments for the options or/and command arguments
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
