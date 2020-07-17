# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
import os
import re

from tern.classes.package import Package
from tern.classes.file_data import FileData
from tern.classes.origins import Origins
from tern.utils import rootfs
from tern.utils.general import prop_names


class ImageLayer:
    '''A representation of a container filesystem layer
    attributes:
        diff_id: the sha256 of the layer filesystem
        fs_hash: the hashed contents of the layer filesystem - default to empty
        string if there is no tarball of the layer filesystem
        packages: list of objects of type Package (package.py)
        origins: list of NoticeOrigin objects (origins.py)
        tar_file: the path to the layer filesystem tarball
        created_by: sometimes the metadata will contain a created_by
        key containing the command that created the filesystem layer
        import_image: if the layer is imported from another image
        this is a pointer to that image. In Python terms it is just the
        name of the Image object or any object that uses this layer
        Based on how container image layers are created, this is usually the
        last layer of the image that was imported
        import_str: The string from a build tool (like a Dockerfile) that
        layer_index: The index position of the layer in relationship to the
        other layers in the image. The base OS would be layer 1.
        created this layer by importing it from another image
        files_analyzed: whether the files in this layer are analyzed or not
        analyzed_output: the result of the file analysis
        files: a list of files included in the image layer
        checksum_type: the digest algorithm used to create the image layer
        checksum
        checksum: the checksum
        checksums: a dictionary of the form {<checksum_type>: <checksum>}
        extension_info: a dictionary contains extension info such as extension
        header info{<headers>: <set_of_header_strings>}
    methods:
        add_package: adds a package to the layer
        remove_package: removes a package from the layer
        to_dict: returns a dict representation of the instance
        get_package_names: returns a list of package names
        gen_fs_hash: calculate the filesystem hash
        add_file: adds a file to the layer
        remove_file: given the file path, remove a file object from the
        list of files in this layer
        get_file_paths: Get a list of file paths in the image layer
        set_checksum: set the checksum of the image layer given the checksum
        type
        add_checksums: add new checksums in the existing list of the checksums
        '''

    def __init__(self, diff_id, tar_file=None, created_by=None):
        self.__diff_id = diff_id
        self.__fs_hash = ''
        self.__tar_file = tar_file
        self.__created_by = created_by
        self.__packages = []
        self.__files = []
        self.__origins = Origins()
        self.__import_image = None
        self.__import_str = ''
        self.__layer_index = ''
        self.__pkg_format = ''
        self.__os_guess = ''
        self.__files_analyzed = False
        self.__analyzed_output = ''
        self.__checksum_type = ''
        self.__checksum = ''
        self.__checksums = {}
        self.__extension_info = {}

    @property
    def diff_id(self):
        return self.__diff_id

    @property
    def packages(self):
        return self.__packages

    @property
    def files(self):
        return self.__files

    @property
    def fs_hash(self):
        return self.__fs_hash

    @property
    def origins(self):
        return self.__origins

    @property
    def tar_file(self):
        return self.__tar_file

    @property
    def created_by(self):
        return self.__created_by

    @property
    def checksum_type(self):
        return self.__checksum_type

    @property
    def checksum(self):
        return self.__checksum

    @property
    def checksums(self):
        return self.__checksums

    @property
    def extension_info(self):
        return self.__extension_info

    @extension_info.setter
    def extension_info(self, extension_info):
        self.__extension_info = extension_info

    @created_by.setter
    def created_by(self, create_string):
        self.__created_by = create_string

    @property
    def import_image(self):
        return self.__import_image

    @import_image.setter
    def import_image(self, import_image):
        self.__import_image = import_image

    @property
    def import_str(self):
        return self.__import_str

    @import_str.setter
    def import_str(self, import_str):
        self.__import_str = import_str

    @property
    def layer_index(self):
        return self.__layer_index

    @layer_index.setter
    def layer_index(self, layer_index):
        self.__layer_index = layer_index

    @property
    def pkg_format(self):
        return self.__pkg_format

    @pkg_format.setter
    def pkg_format(self, pkg_format):
        self.__pkg_format = pkg_format

    @property
    def os_guess(self):
        return self.__os_guess

    @os_guess.setter
    def os_guess(self, os_guess):
        self.__os_guess = os_guess

    @property
    def analyzed_output(self):
        return self.__analyzed_output

    @analyzed_output.setter
    def analyzed_output(self, analyzed_output):
        if isinstance(analyzed_output, str):
            self.__analyzed_output = analyzed_output
        else:
            raise ValueError('analyzed_output should be a string')

    @property
    def files_analyzed(self):
        return self.__files_analyzed

    @files_analyzed.setter
    def files_analyzed(self, x):
        if isinstance(x, bool):
            self.__files_analyzed = x
        else:
            raise ValueError('files_analyzed should be boolean')

    def set_checksum(self, checksum_type='', checksum=''):
        '''Set the checksum type and checksum of the image layer'''
        # TODO: calculate the checksum if not given
        self.__checksum_type = checksum_type
        self.__checksum = checksum

    def add_checksums(self, checksums):
        '''Add a checksum dictionary to checksums property'''
        for key, value in checksums.items():
            self.__checksums[key.lower()] = value.lower()

    def add_package(self, package):
        if isinstance(package, Package):
            if package.name not in self.get_package_names():
                self.__packages.append(package)
        else:
            raise TypeError('Object type is {0}, should be Package'.format(
                type(package)))

    def remove_package(self, package_name):
        rem_index = 0
        success = False
        for index in range(0, len(self.__packages)):
            if self.packages[index].name == package_name:
                rem_index = index
                success = True
                break
        if success:
            self.__packages.remove(self.__packages[rem_index])
        return success

    def add_file(self, filedata):
        if isinstance(filedata, FileData):
            if filedata.path not in self.get_file_paths():
                self.__files.append(filedata)
        else:
            raise TypeError('Object type is {0}, should be FileData'.format(
                type(filedata)))

    def get_file_paths(self):
        '''Get the list of file paths in this layer'''
        file_path_list = []
        for f in self.files:
            file_path_list.append(f.path)
        return file_path_list

    def remove_file(self, file_path):
        '''Given the file path, remove the file object from the list of files
        in the layer'''
        rem_index = 0
        success = False
        for index in range(0, len(self.__files)):
            if self.__files[index].path == file_path:
                rem_index = index
                success = True
                break
        if success:
            self.__files.remove(self.__files[rem_index])
        return success

    def to_dict(self, template=None):
        '''Return a dictionary representation of the image layer object'''
        layer_dict = {}
        # for packages call each package object's to_dict method
        pkg_list = [pkg.to_dict(template) for pkg in self.packages]
        # for files call each FileData object's to_dict method
        file_list = [f.to_dict(template) for f in self.files]
        if template:
            # use the template mapping for key names
            for key, prop in prop_names(self):
                if prop in template.image_layer().keys():
                    layer_dict.update(
                        {template.image_layer()[prop]: self.__dict__[key]})
            # update the 'origins' if it exists in the mapping
            if 'origins' in template.image_layer().keys():
                layer_dict.update(
                    {template.image_layer()['origins']: self.origins.to_dict(
                    )})
            # update the 'packages' if it exists in the mapping
            if 'packages' in template.image_layer().keys():
                layer_dict.update(
                    {template.image_layer()['packages']: pkg_list})
            # update the 'files' if it exists in the mapping
            if 'files' in template.image_layer().keys():
                layer_dict.update(
                    {template.image_layer()['files']: file_list})
        else:
            # directly use property names
            for key, prop in prop_names(self):
                layer_dict.update({prop: self.__dict__[key]})
            # update with 'packages' info
            layer_dict.update({'packages': pkg_list})
            # update with 'files' info
            layer_dict.update({'files': file_list})
            # take care of the 'origins' property
            layer_dict.update({'origins': self.origins.to_dict()})
            # take care of the 'extension_info' property
            layer_dict.update({'extension_info': self.extension_info})
        return layer_dict

    def get_package_names(self):
        '''Get the list of package names in this layer'''
        pkg_list = []
        for pkg in self.packages:
            pkg_list.append(pkg.name)
        return pkg_list

    def gen_fs_hash(self):
        '''Get the filesystem hash if the image class was created with a
        tar_file'''
        if self.__tar_file:
            fs_dir = rootfs.get_untar_dir(self.__tar_file)
            tar_file = rootfs.get_layer_tar_path(self.__tar_file)
            rootfs.extract_tarfile(tar_file, fs_dir)
            self.__fs_hash = rootfs.calc_fs_hash(fs_dir)

    def add_files(self):
        '''Get all the files present in a layer and store
        them as a list of FileData objects'''
        fs_path = rootfs.get_untar_dir(self.__tar_file)
        hash_file = os.path.join(os.path.dirname(fs_path),
                                 self.__fs_hash) + '.txt'
        pattern = re.compile(r'([\w\-|]+)\s+(.+)')
        with open(hash_file) as f:
            content = f.readlines()
        for line in content:
            m = pattern.search(line)
            if m:
                # m.group(2) contains the file path
                # m.group(1) contains the extattrs and checksum
                file_data = FileData(os.path.basename(m.group(2)),
                                     os.path.relpath(m.group(2), '.'))
                # attrs_tuple contains (extattrs, '|', checksum)
                attrs_tuple = m.group(1).rpartition('|')
                file_data.set_checksum('sha256', attrs_tuple[2])
                file_data.extattrs = attrs_tuple[0]
                self.add_file(file_data)

    def get_layer_workdir(self):
        # If the layer is created by a WORKDIR command then return the workdir
        match = re.search(r"\bWORKDIR\ (\/\w+)+\b", self.created_by)
        if match:
            return match.group().split()[1]
        return None
