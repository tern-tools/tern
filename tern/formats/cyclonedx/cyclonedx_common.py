# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Patrick Dwyer. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Common functions that are useful for CycloneDX document creation
"""

import datetime
import uuid
from tern.utils import general
import spdx_license_list
sll = spdx_license_list.LICENSES

###################
# General Helpers #
###################


# document level tool information
metadata_tool = {
    'vendor': 'Tern Tools',
    'name': 'Tern',
    'version': general.get_git_rev_or_version()[1]
}


# keys are what Tern uses, values what CycloneDX uses
hash_type_mapping = {
    'md5': 'MD5',
    'sha1': 'SHA-1',
    'sha256': 'SHA-256',
}


purl_types_with_namespaces = [
    'deb',
    'rpm',
    'apk',
]


purl_names_in_lowercase = [
    'deb',
    'go',
    'npm',
    'pypi',
    'rpm',
]


def get_serial_number():
    ''' Return a randomly generated CycloneDX BOM serial number '''
    return 'urn:uuid:' + str(uuid.uuid4())


def get_purl_name(name, pkg_format):
    '''Some purl types require that package names always be lowercased. Given
    a package format and a corresponding name for a package of that format,
    return a lowercased version of the package name if the purl spec requires
    it. Otherwise, just return the original package name.'''
    if pkg_format in purl_names_in_lowercase:
        return name.lower()
    return name


def get_timestamp():
    ''' Return a timestamp suitable for the BOM timestamp '''
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def get_hash(checksum_type, checksum):
    ''' Return a CycloneDX hash object from Tern checksum values '''
    hash_algorithm = hash_type_mapping.get(checksum_type, None)
    return None if hash_algorithm is None else {'alg': hash_algorithm, 'content': checksum}


def get_property(name, value):
    ''' Return a CycloneDX property object '''
    return {'name': name, 'value': value}


def get_purl_namespace(os_guess, pkg_format):
    if pkg_format in purl_types_with_namespaces:
        return os_guess.partition(' ')[0].lower()
    return None


def get_os_guess(image_obj):
    return image_obj.layers[0].os_guess or None


def get_license_from_name(name):
    if sll.get(name) is None:
        return {'license': {'name': name}}
    else:
        return {'license': {'id': name}}
