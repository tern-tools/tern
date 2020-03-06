# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import datetime

from tern.classes.origins import Origins
from tern.utils.general import prop_names


class FileData:
    '''A file existing within a container image layer
    If any file level analysis is done then most of the attributes can be
    filled up. If no analysis is done, we would still have at the minimum the
    file name and path
    attributes:
        name: file name
        path: path to the file
        date: the creation date of the file
        checksum_type: the digest algorithm used to create the file checksum
        checksum: the checksum
        version_control: the type of version control tool used. Left blank if
        the file was downloaded using a package manager or from a website.
        version: the version of the file under version control. If it came
        with a package the version would be the same as the package version.
        file_type: this is a string describing what type of file this is
        licenses: A list of licenses that may be detected or is known
        license_expressions: This is a SPDX term used to describe how one or
        more licenses together should be understood. This list may be left
        blank.
        copyrights: a list of copyright strings
        authors: a list of authors if known
        packages: a list of packages where this file could come from
        urls: a list of urls from where this file could come from

    methods:
        to_dict: returns a dictionary representation of the instance
        set_version: set the version of the file given the version control
        system used
        set_checksum: set the checksum of the file given the checksum type'''
    def __init__(self,
                 name,
                 path,
                 date='',
                 file_type=''):
        self.__name = name
        self.__path = path
        self.date = date
        self.__file_type = file_type
        self.__checksum_type = ''
        self.__checksum = ''
        self.__version_control = ''
        self.__version = ''
        self.__extattrs = ''
        self.licenses = []
        self.license_expressions = []
        self.copyrights = []
        self.authors = []
        self.packages = []
        self.urls = []
        self.__origins = Origins()

    @property
    def name(self):
        return self.__name

    @property
    def path(self):
        return self.__path

    @property
    def date(self):
        return self.__date

    @property
    def extattrs(self):
        return self.__extattrs

    @extattrs.setter
    def extattrs(self, extattrs):
        self.__extattrs = extattrs

    @date.setter
    def date(self, date):
        '''Set the date if a date string exists'''
        if date:
            try:
                datetime.datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Incorrect date format, should be YYYY-MM-DD")
        self.__date = date

    @property
    def checksum_type(self):
        return self.__checksum_type

    @property
    def checksum(self):
        return self.__checksum

    @property
    def version_control(self):
        return self.__version_control

    @property
    def version(self):
        return self.__version

    @property
    def file_type(self):
        return self.__file_type

    @file_type.setter
    def file_type(self, file_type):
        self.__file_type = file_type

    @property
    def origins(self):
        return self.__origins

    def set_checksum(self, checksum_type='', checksum=''):
        '''Set the checksum type and checksum of the file'''
        # TODO: calculate the checksum if not given
        self.__checksum_type = checksum_type
        self.__checksum = checksum

    def set_version(self, version_control='', version=''):
        '''Set the version control and version of the file'''
        # TODO: find the version given the version control system
        self.__version_control = version_control
        self.__version = version

    def to_dict(self, template=None):
        '''Return a dictionary version of the FileData object
        If given an object which is a subclass of Template then map
        the keys to the FileData class properties'''
        file_dict = {}
        if template:
            # loop through object properties
            for key, prop in prop_names(self):
                # check if the property is in the mapping
                if prop in template.file_data().keys():
                    file_dict.update(
                        {template.file_data()[prop]: self.__dict__[key]})
            # update the 'origins' part if it exists in the mapping
            if 'origins' in template.file_data().keys():
                file_dict.update(
                    {template.file_data()['origins']: self.origins.to_dict()})
        else:
            # don't map, just use the property name as the key
            for key, prop in prop_names(self):
                file_dict.update({prop: self.__dict__[key]})
            file_dict.update({'origins': self.origins.to_dict()})
        return file_dict
