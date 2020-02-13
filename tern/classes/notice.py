# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.utils.general import prop_names


class NoticeException(Exception):
    '''Base notice exception'''


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

    def to_dict(self, template=None):
        notice_dict = {}
        if template:
            # loop through object properties
            for key, prop in prop_names(self):
                # check if the property is in the mapping
                if prop in template.notice().keys():
                    notice_dict.update(
                        {template.notice()[prop]: self.__dict__[key]})
        else:
            # don't map, just use the property name as the key
            for key, prop in prop_names(self):
                notice_dict.update({prop: self.__dict__[key]})
            # special case - don't include 'levels'
            notice_dict.pop('levels')
        return notice_dict
