# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import datetime

from tern.classes.notice import Notice
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
        short_file_type: this is a short string describing what type of file
        this is. This should be one of the following:
            SOURCE, BINARY, ARCHIVE, TEXT, OTHER
        licenses: A list of licenses that may be detected or is known
        license_expressions: This is a SPDX term used to describe how one or
        more licenses together should be understood. This list may be left
        blank.
        copyrights: a list of copyright strings
        authors: a list of authors if known
        packages: a list of packages where this file could come from
        urls: a list of urls from where this file could come from
        checksums: a dictionary of the form {<checksum_type>: <checksum>,...}
        checksum types and checksums are stored in lower case

    methods:
        to_dict: returns a dictionary representation of the instance
        set_version: set the version of the file given the version control
        system used
        set_checksum: set the checksum of the file given the checksum type
        get_checksum: get the checksum that matches the checksum type from
        the property 'checksums'
        fill: fill data into the object instance from a dictionary'''
    def __init__(self,
                 name,
                 path,
                 date='',
                 file_type=''):
        self.__name = name
        self.__path = path
        self.date = date
        self.__file_type = file_type
        self.__short_file_type = ''
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
        self.__checksums = {}
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
    def checksums(self):
        return self.__checksums

    @property
    def short_file_type(self):
        return self.__short_file_type

    @short_file_type.setter
    def short_file_type(self, short_file_type):
        '''short_file_type should be one of these:
            SOURCE, BINARY, ARCHIVE, TEXT, OTHER'''
        allowed_file_types = ('SOURCE', 'BINARY', 'ARCHIVE', 'TEXT', 'OTHER')
        if short_file_type not in allowed_file_types:
            raise ValueError(
                "Incorrect short file type name, should be "
                "SOURCE, BINARY, ARCHIVE, TEXT or OTHER")
        self.__short_file_type = short_file_type

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

    def add_checksums(self, checksums):
        '''Add a checksum dictionary to checksums property'''
        for key, value in checksums.items():
            self.__checksums[key.lower()] = value.lower()

    def get_checksum(self, hash_type):
        '''Given a hash type, return the checksum. If the hash type is not
        available, return None'''
        return self.__checksums.get(hash_type.lower(), None)

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

    def __fill_properties(self, file_dict):
        '''Check to see if the dictionary keys have all the properties
        listed. If not then put a Notice object in the list of Origins'''
        for key, prop in prop_names(self):
            if prop not in ('name', 'origins', 'path'):
                if prop not in file_dict.keys():
                    self.origins.add_notice_to_origins(
                        self.name, Notice(
                            "No metadata for key: {}".format(prop), 'warning'))
                else:
                    self.__dict__[key] = file_dict[prop]

    def fill(self, file_dict):
        '''The file dict looks like this:
            name: <name>
            path: <path to file>
            date: <date>
            file_type: <file_type>
            short_file_type: <short_file_type>
            checksum: <checksum>
            checksum_type: <checksum_type>
            version_control: <version_control>
            version: <version>
            extattrs: <extattrs>
            licenses: <licenses>
            license_expressions: <license_expressions>
            copyrights: <copyrights>
            authors: <authors>
            packages: <packages>
            urls: <urls>
            checksums: <checksums>
        the way to use this method is to instantiate the class with the
        name and path and then give it a file_data dictionary to fill
        in the rest return true if package name is the same as the one
        used to instantiate the object, false if not'''
        success = True
        if self.name == file_dict['name'] and self.path == file_dict['path']:
            self.__fill_properties(file_dict)
        else:
            success = False
        return success

    def merge(self, other):
        '''Compare another FileData object to this instance. If the file path
        is the same, we fill in the rest of the data excluding the checksum,
        version control data and the extended attributes. This method can
        be used in situations where an external scanner is used to collect
        file level data that we don't collect ourselves'''
        if not isinstance(other, FileData):
            return False
        if (self.path == other.path):
            self.date = other.date
            self.file_type = other.file_type
            if other.short_file_type:
                self.short_file_type = other.short_file_type
            self.licenses = other.licenses
            self.license_expressions = other.license_expressions
            self.copyrights = other.copyrights
            self.authors = other.authors
            self.packages = other.packages
            self.urls = other.urls
            self.add_checksums(other.checksums)
            # collect notices
            for o in other.origins.origins:
                for n in o.notices:
                    self.origins.add_notice_to_origins(o.origin_str, n)
            return True
        return False

    def is_equal(self, other):
        '''Returns true if the two FileData objects have the same name, path
        and checksum properties'''
        if not isinstance(other, FileData):
            return False
        return (self.name == other.name and self.path == other.path and
                self.checksum == other.checksum)
