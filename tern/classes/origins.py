# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.classes.notice_origin import NoticeOrigin


class Origins:
    '''An class containing a list of NoticeOrigin objects
    attributes:
        origins: a list of NoticeOrigin objects
    methods:
        get_origin: given the string return the origin
        add_notice_to_origin:
            If a NoticeOrigin object exists in the list of NoticeOrigin
            objects, then the Notice object will be added to that
            NoticeOrigin - return true if this happens
            If there is no NoticeOrigin object with the given string,
            create a NoticeOrigin object and add it to the list of
            origins
        add_notice_origin: add an empty NoticeOrigin object
        is_empty: check if there are any notices
        to_dict: return a dict representation of the object
    '''
    def __init__(self):
        self.__origins = []

    @property
    def origins(self):
        return self.__origins

    def get_origin(self, string):
        for orij in self.__origins:
            if orij.origin_str == string:
                return orij
        return None

    def add_notice_to_origins(self, orig_string, notice):
        orij = self.get_origin(orig_string)
        if orij:
            orij.add_notice(notice)
        else:
            notice_orij = NoticeOrigin(orig_string)
            notice_orij.add_notice(notice)
            self.__origins.append(notice_orij)

    def add_notice_origin(self, orig_string):
        if not self.get_origin(orig_string):
            self.__origins.append(NoticeOrigin(orig_string))

    def is_empty(self):
        empty = True
        if self.__origins:
            for orij in self.__origins:
                if orij.notices:
                    empty = False
                    break
        return empty

    def to_dict(self, template=None):
        return [origin.to_dict(template) for origin in self.origins]
