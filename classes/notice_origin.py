'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

from report import formats

class NoticeOrigin(object):
    '''The origin of a notice
    attributes:
        origin_str: the origin string, from the input or the environment or
        the configuration
        notices: a list of Notice objects
    methods:
        collate_notices: print all the notices for this origin and
    '''
    def __init__(self, origin_str):
        self.__origin_str = origin_str
        self.__notices = []

    @property
    def origin_str(self):
        return self.__origin_str

    @property
    def notices(self):
        return self.__notices

    def add_notice(self, notice):
        self.__notices.append(notice)

    def print_notices(self):
        '''Using the notice format, return a formatted string'''
        info = ''
        warnings = ''
        errors = ''
        hints = ''
        for notice in self.notices:
            if notice.level == 'info':
                info = info + notice.message
            if notice.level == 'warning':
                warnings = warnings + notice.message
            if notice.level == 'error':
                errors = errors + notice.message
            if notice.level == 'hints':
                hints = hints + notice.message
        notice_msg = formats.notice_format(
            origin=self.origin, info=info, warnings=warnings, errors=errors,
            hints=hints)
        return notice_msg
