# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.report import formats
from tern.utils.general import prop_names
from tern.classes.notice import Notice


class NoticeOrigin:
    '''The origin of a notice
    attributes:
        origin_str: the origin string, from the input or the environment or
        the configuration
        notices: a list of Notice objects
    methods:
        print_notices: print all the notices for this origin and
        to_dict: return a dict representation of the object
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
        if isinstance(notice, Notice):
            self.__notices.append(notice)
        else:
            raise TypeError('Object type is {0}, should be Notice'.format(
                type(notice)))

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
            if notice.level == 'hint':
                hints = hints + notice.message
        notice_msg = formats.notice_format.format(
            origin=self.origin_str,
            info=info,
            warnings=warnings,
            errors=errors,
            hints=hints)
        return notice_msg

    def to_dict(self, template=None):
        no_dict = {}
        # for packages call each package object's to_dict method
        notice_list = [notice.to_dict(template) for notice in self.notices]
        if template:
            # use the template mapping for key names
            for key, prop in prop_names(self):
                if prop in template.notice_origin().keys():
                    no_dict.update(
                        {template.notice_origin()[prop]: self.__dict__[key]})
            # update the 'notices' if it exists in the mapping
            if 'notices' in template.notice_origin().keys():
                no_dict.update(
                    {template.notice_origin()['notices']: notice_list})
        else:
            # directly use property names
            for key, prop in prop_names(self):
                no_dict.update({prop: self.__dict__[key]})
            # update with 'notices' info
            no_dict.update({'notices': notice_list})
        return no_dict
