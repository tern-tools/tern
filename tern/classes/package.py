#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

from tern.classes.origins import Origins
from tern.classes.template import Template
from tern.utils.general import prop_names


class Package:
    '''A package installed within a Docker image layer
    attributes:
        name: package name
        version: package version
        license: package license
        src_url: package source url
        origins: a list of NoticeOrigin objects

    methods:
        to_dict: returns a dict representation of the instance
        fill: instantiates a package object given a dict representation.
        is_equal: compares two package objects.'''
    def __init__(self, name):
        self.__name = name
        self.__version = ''
        self.__license = ''
        self.__src_url = ''
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
    def license(self):
        return self.__license

    @license.setter
    def license(self, license):  # pylint: disable=redefined-builtin
        self.__license = license

    @property
    def src_url(self):
        return self.__src_url

    @src_url.setter
    def src_url(self, src_url):
        self.__src_url = src_url

    @property
    def origins(self):
        return self.__origins

    def to_dict(self, template=None):
        '''Return a dictionary version of the Package object
        If given an object which is a subclass of Template then map
        the keys to the Package class properties'''
        pkg_dict = {}
        # get a key mapping
        if issubclass(template, Template):
            mapping = template.package()
        # loop through object properties
        for key, prop in prop_names(self):
            # check if the property is in the mapping
            if mapping and prop in mapping.keys():
                pkg_dict.update({mapping[prop]: self.__dict__[key]})
            else:
                pkg_dict.update({prop: self.__dict__[key]})
        # update the 'origins' part if it exists
        if 'origins' in mapping.keys():
            pkg_dict.update({mapping['origins']: self.origins.to_dict()})
        else:
            pkg_dict.update({'origins': self.origins.to_dict()})
        return pkg_dict

    def fill(self, package_dict):
        '''The package dict looks like this:
            name: <name>
            version: <version>
            license: <license string>
            src_url: <source url>
        the way to use this method is to instantiate the class with the
        name and then give it a package dictionary to fill in the rest
        return true if package name is the same as the one used to instantiate
        the object, false if not'''
        success = True
        if self.name == package_dict['name']:
            self.version = package_dict['version']
            self.license = package_dict['license']
            self.src_url = package_dict['src_url']
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
