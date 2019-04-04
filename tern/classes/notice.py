#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#


class NoticeException(Exception):
    '''Base notice exception'''
    pass


class LevelException(NoticeException):
    '''Exception for illegal notices'''
    def __init__(self, level, message):
        self.level = level
        self.message = message


class Notice:
    '''A notice for reporting purposes
    attributes:
        message: the notice message
        level: notice level - error, warning or hint
            error: cannot continue further
            warning: will try to continue from here
            info: information only
            hint: message on how to make the results better
    methods:
        to_dict: returns a dict representation of the object
    '''
    def __init__(self, message='', level='info'):
        self.__message = message
        self.__level = ''
        self.__levels = ['error', 'warning', 'hint', 'info']
        self.level = level

    @property
    def message(self):
        return self.__message

    @message.setter
    def message(self, message):
        self.__message = message

    @property
    def level(self):
        return self.__level

    @level.setter
    def level(self, level):
        if level in self.__levels:
            self.__level = level
        else:
            raise LevelException(level, 'Illegal Level')

    def to_dict(self):
        notice_dict = {}
        notice_dict.update({'message': self.message})
        notice_dict.update({'level': self.level})
        return notice_dict
