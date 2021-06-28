# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.classes.file_data import FileData
from tern.classes.notice import Notice
from tern.classes.origins import Origins
from tern.utils.general import prop_names


class Package:
    '''A package installed within a Docker image layer
    attributes:
        name: package name
        version: package version
        pkg_license: package license that is declared
        copyright: copyright text
        proj_url: package source url
        download_url: package download url
        origins: a list of NoticeOrigin objects
        checksum: checksum as package property
        files: list of files in a package
        pkg_licenses: all licenses found within a package

    methods:
        to_dict: returns a dict representation of the instance
        fill: instantiates a package object given a dict representation.
        is_equal: compares two package objects.
        get_file_paths: Returns a list of file paths
        add_file: Add a file to list of files
        remove_file: Removes a file from a list of files
        '''
    def __init__(self, name):
        self.__name = name
        self.__version = ''
        self.__pkg_license = ''
        self.__copyright = ''
        self.__proj_url = ''
        self.__download_url = ''
        self.__checksum = ''
        self.__origins = Origins()
        self.__files = []
        self.__pkg_licenses = []
        self.__pkg_format = ''

    @property
    def name(self):
        return self.__name

    @property
    def files(self):
        return self.__files

    @files.setter
    def files(self, files):
        self.__files = files

    @property
    def version(self):
        return self.__version

    @version.setter
    def version(self, version):
        self.__version = version

    @property
    def pkg_license(self):
        return self.__pkg_license

    @property
    def pkg_licenses(self):
        return self.__pkg_licenses

    @pkg_license.setter
    def pkg_license(self, pkg_license):
        self.__pkg_license = pkg_license

    @pkg_licenses.setter
    def pkg_licenses(self, pkg_licenses):
        self.__pkg_licenses = pkg_licenses

    @property
    def copyright(self):
        return self.__copyright

    @copyright.setter
    def copyright(self, text):
        self.__copyright = text

    @property
    def proj_url(self):
        return self.__proj_url

    @proj_url.setter
    def proj_url(self, proj_url):
        self.__proj_url = proj_url

    @property
    def download_url(self):
        return self.__download_url

    @download_url.setter
    def download_url(self, url):
        self.__download_url = url

    @property
    def origins(self):
        return self.__origins

    @property
    def checksum(self):
        return self.__checksum

    @checksum.setter
    def checksum(self, checksum):
        self.__checksum = checksum

    @property
    def pkg_format(self):
        return self.__pkg_format

    @pkg_format.setter
    def pkg_format(self, pkg_format):
        self.__pkg_format = pkg_format

    def get_file_paths(self):
        """Return a list of paths of all the files in a package"""
        return [f.path for f in self.__files]

    def add_file(self, file):
        """Add a file to the list of files present in a package"""
        if isinstance(file, FileData):
            if file.path not in self.get_file_paths():
                self.files.append(file)
        else:
            raise TypeError('Object type is {0}, should be FileData'.format(
                type(file)))

    def remove_file(self, file_path):
        """Remove a file from the list of files present in a package"""
        for file in self.__files:
            if file.path == file_path:
                self.__files.remove(file)
                return True
        return False

    def to_dict(self, template=None):
        '''Return a dictionary version of the Package object
        If given an object which is a subclass of Template then map
        the keys to the Package class properties'''
        pkg_dict = {}
        file_list = [f.to_dict(template) for f in self.__files]
        if template:
            # loop through object properties
            for key, prop in prop_names(self):
                # check if the property is in the mapping
                if prop in template.package().keys():
                    pkg_dict.update(
                        {template.package()[prop]: self.__dict__[key]})
            # update the 'origins' part if it exists in the mapping
            if 'origins' in template.package().keys():
                pkg_dict.update(
                    {template.package()['origins']: self.origins.to_dict()})
            # update the 'files' part if it exists in the mapping
            if 'files' in template.package().keys():
                pkg_dict.update(
                    {template.package()['files']: file_list})
        else:
            # don't map, just use the property name as the key
            for key, prop in prop_names(self):
                pkg_dict.update({prop: self.__dict__[key]})
            pkg_dict.update({'origins': self.origins.to_dict()})
            pkg_dict.update({'files': file_list})
        return pkg_dict

    def __fill_properties(self, package_dict):
        '''Check to see if the dictionary keys have all the properties
        listed. If not then put a Notice object in the list of Origins
        package_dict should not contain 'name' '''
        for key, prop in prop_names(self):
            if prop not in ('name', 'origins'):
                if prop not in package_dict.keys():
                    self.origins.add_notice_to_origins(
                        self.name, Notice(
                            "No metadata for key: {}".format(prop), 'warning'))
                else:
                    self.__dict__[key] = package_dict[prop]

    def fill(self, package_dict):
        '''The package dict looks like this:
            name: <name>
            version: <version>
            pkg_license: <package license string>
            copyright: <package copyright text>
            proj_url: <project url>
            files: <package files>
        the way to use this method is to instantiate the class with the
        name and then give it a package dictionary to fill in the rest
        return true if package name is the same as the one used to instantiate
        the object, false if not'''
        if self.name == package_dict['name']:
            # update the package dictionary with file info
            file_list = package_dict.get('files', False)
            if file_list:
                fd_list = []
                for file_dict in file_list:
                    fd = FileData(file_dict['name'], file_dict['path'])
                    fd.fill(file_dict)
                    fd_list.append(fd)
                package_dict['files'] = fd_list
            self.__fill_properties(package_dict)
            return True
        return False

    def is_equal(self, other):
        '''This method performs a deep comparison between two objects by
        iterating over the dictionary for each object returned by to_dict
        and comparing the vales for each key in both. This function will only
        return true if every key value pair matches between the two
        dictionaries.'''
        other_pkg_dict = other.to_dict()
        for key, value in self.to_dict().items():
            if key == 'pkg_licenses':
                # There may be more than one package license. Therefore,
                # we must sort pkg_licenses before comparison
                value.sort()
                other_pkg_dict[key].sort()
            if value != other_pkg_dict[key]:
                return False
        return True

    def merge(self, other):
        '''Compare another Package object to this instance. If the name and
        version are the same, we use the other object to fill in missing
        metadata in the first one excluding the files and origins. This
        method can be used in situations where an external scanner is used to
        collect package data that we didn't find ourselves'''
        if not isinstance(other, Package):
            return False
        if self.name == other.name and self.version == other.version:
            other_pkg_dict = other.to_dict()
            for key, value in self.to_dict().items():
                if value == '' and other_pkg_dict[key] != '':
                    setattr(self, key, other_pkg_dict[key])
                    for lic in other.pkg_licenses:
                        if lic not in self.pkg_licenses:
                            self.pkg_licenses.append(lic)
            return True
        return False
