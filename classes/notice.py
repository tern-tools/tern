'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

class NoticeException(Exception):
    '''Base notice exception'''
    pass


class LevelException(NoticeException):
    '''Exception for illegal notices'''
    def __init__(self, level, message):
        self.level = level
        self.message = message


class Notice(object):
    '''A notice for reporting purposes
    attributes:
        origin: what the notice is referencing - the image, the image layer id
        the dockerfile line
        message: the notice message
        level: notice level - error, warning or hint
            error: cannot continue further
            warning: will try to continue from here
            hint: message on how to make the results better
    '''
    def __init__(self):
        self.__origin = ''
        self.__message = ''
        self.__level = ''
        self.__levels = ['error', 'warning', 'hint']

    @property
    def origin(self):
        return self.__origin

    @origin.setter
    def origin(self, origin):
        self.__origin = origin

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
