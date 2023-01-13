# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2022 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
import os
import re

from tern.classes.package import Package
from tern.classes.file_data import FileData
from tern.classes.origins import Origins
from tern.utils import rootfs
from tern.utils import constants
from tern.utils.general import prop_names
from tern.utils.externals import add_purl


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
        image_layout: Indicates the image layout on disk in order to read
        the layer filesystem. This is either "oci" or "docker".
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
        get_untar_dir: returns the path where the contents of the layer are
        untarred.
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
        self.__image_layout = 'oci'
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
        self.__layer_index = str(layer_index)

    @property
    def image_layout(self):
        return self.__image_layout

    @image_layout.setter
    def image_layout(self, image_layout):
        if image_layout in ('oci', 'docker'):
            self.__image_layout = image_layout
        else:
            self.__image_layout = 'oci'

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
                purl = add_purl(package.name, package.version)
                package.external_refs.append(purl)
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
        for index, _ in enumerate(self.__files):
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

    def get_untar_dir(self):
        """Get the directory where contents of the image layer are untarred"""
        # the untar directory is based on the image layout
        if self.image_layout == 'docker':
            # Images built with Kaniko and its tarPath parameter identify
            # as Docker image based on the metadata format, but keep their
            # layer tar files in the root of the main tar file.
            # So we will make sure if there's no subdir for the layer tar
            # files, we use the first part of the file name as dir name.
            # This is to prevent overwriting the extracted layers on every
            # subsequent layer inspection.
            subdir_name = os.path.dirname(self.tar_file)
            if not subdir_name:
                subdir_name = self.tar_file.split('.', 1)[0]
            return os.path.join(rootfs.get_working_dir(),
                                subdir_name,
                                constants.untar_dir)
        # For OCI layouts, the tar file may be at the root of the directory
        # So we will return a path one level deeper
        return os.path.join(
            rootfs.get_working_dir(), self.layer_index, constants.untar_dir)

    def gen_fs_hash(self):
        '''Get the filesystem hash if the image class was created with a
        tar_file'''
        if self.tar_file:
            fs_dir = self.get_untar_dir()
            # make directory structure if it doesn't exist
            if not os.path.exists(fs_dir):
                os.makedirs(fs_dir)
            tar_file = os.path.join(rootfs.get_working_dir(), self.tar_file)
            rootfs.extract_tarfile(tar_file, fs_dir)
            self.__fs_hash = rootfs.calc_fs_hash(fs_dir)

    def _parse_hash_content(self, content):
        """This is an internal function to parse the content of the hash
        and return a list of FileData objects
        The content consists of lines of the form:
        permissions|uid|gid|size|hard links|  sha256sum  filepath xattrs
        where xattrs is the list of extended attributes for the file
        The extended attributes start with a '# file' indicator, followed
        by a list of key-value pairs separated by newlines. For now, we will
        conserve the key-value pair list as they appear and separate
        each one by a comma"""
        file_list = []
        # keep track of where we are on the list of files
        index = 0
        # loop through the content
        while content:
            line = content.pop(0)
            if "# file" in line:
                # collect the extended attributes
                xattrlist = []
                xattrline = content.pop(0)
                while xattrline != '\n':
                    if 'selinux' not in xattrline:
                        xattrlist.append(xattrline.strip())
                    xattrline = content.pop(0)
                # when we break out of the extended attributes loop
                # we combine the results and update the FileData object
                # existing in the previous index
                file_list[index-1].extattrs = file_list[index-1].extattrs + \
                    "  " + ','.join(xattrlist)
            else:
                # collect the regular attributes
                file_info = line[:-1].split('  ')
                file_data = FileData(os.path.basename(file_info[2]),
                                     os.path.relpath(file_info[2], '.'))
                file_data.set_checksum('sha256', file_info[1])
                file_data.set_whiteout()
                file_list.append(file_data)
                index = index + 1
        return file_list

    def add_files(self):
        '''Get all the files present in a layer and store
        them as a list of FileData objects'''
        fs_path = self.get_untar_dir()
        hash_file = os.path.join(os.path.dirname(fs_path),
                                 self.__fs_hash) + '.txt'
        with open(hash_file, encoding='utf-8') as f:
            content = f.readlines()
        file_list = self._parse_hash_content(content)
        for file_data in file_list:
            self.add_file(file_data)

    def get_layer_workdir(self):
        # If the layer is created by a WORKDIR command then return the workdir
        match = re.search(r"\bWORKDIR\ (\/\w+)+\b", self.created_by)
        if match:
            return match.group().split()[1]
        return ''
