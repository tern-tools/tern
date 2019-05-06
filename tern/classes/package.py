# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

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
        src_url: package source url
        download_url: package download url
        origins: a list of NoticeOrigin objects

    methods:
        to_dict: returns a dict representation of the instance
        fill: instantiates a package object given a dict representation.
        is_equal: compares two package objects.'''
    def __init__(self, name):
        self.__name = name
        self.__version = ''
        self.__pkg_license = ''
        self.__copyright = ''
        self.__src_url = ''
        self.__download_url = ''
        self.__origins = Origins()

    @property
    def name(self):
        return self.__name

    @property
    def version(self):
        return self.__version

    @version.setter
    def version(self, version):
        self.__version = version

    @property
    def pkg_license(self):
        return self.__pkg_license

    @pkg_license.setter
    def pkg_license(self, pkg_license):
        self.__pkg_license = pkg_license

    @property
    def copyright(self):
        return self.__copyright

    @copyright.setter
    def copyright(self, text):
        self.__copyright = text

    @property
    def src_url(self):
        return self.__src_url

    @src_url.setter
    def src_url(self, src_url):
        self.__src_url = src_url

    @property
    def download_url(self):
        return self.__download_url

    @download_url.setter
    def download_url(self, url):
        self.__download_url = url

    @property
    def origins(self):
        return self.__origins

    def to_dict(self, template=None):
        '''Return a dictionary version of the Package object
        If given an object which is a subclass of Template then map
        the keys to the Package class properties'''
        pkg_dict = {}
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
        else:
            # don't map, just use the property name as the key
            for key, prop in prop_names(self):
                pkg_dict.update({prop: self.__dict__[key]})
            pkg_dict.update({'origins': self.origins.to_dict()})
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
            src_url: <source url>
        the way to use this method is to instantiate the class with the
        name and then give it a package dictionary to fill in the rest
        return true if package name is the same as the one used to instantiate
        the object, false if not'''
        success = True
        if self.name == package_dict['name']:
            self.__fill_properties(package_dict)
        else:
            success = False
        return success

    def is_equal(self, other):
        '''This method performs a deep comparison between two objects by
        iterating over the dictionary for each object returned by to_dict
        and comparing the vales for each key in both. This function will only
        return true if every key value pair matches between the two
        dictionaries.'''
        other_pkg_dict = other.to_dict()
        for key, value in self.to_dict().items():
            if value != other_pkg_dict[key]:
                return False
        return True

    def get_package_id(self):
        '''This method returns a string of the name and version for a package
        represented as "name.version". This method might be helpful when working
        with SPDX documents that require a unique package identifier.'''
        return "{0}.{1}".format(self.name, self.version)
