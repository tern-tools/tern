# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Common functions that are useful for both JSON and Tag-value document creation
"""

import hashlib
import logging
import uuid

from tern.utils import constants
from tern.formats.spdx.spdxtagvalue import formats as spdx_formats

# global logger
logger = logging.getLogger(constants.logger_name)


###################
# General Helpers #
###################

def get_uuid():
    """ Return a UUID string"""
    return str(uuid.uuid4())


def get_string_id(string):
    """ Return a unique identifier for the given string"""
    return hashlib.sha256(string.encode('utf-8')).hexdigest()[-7:]


def get_license_ref(license_string):
    """ For SPDX tag-value format, return a LicenseRef string """
    return 'LicenseRef-' + get_string_id(license_string)


########################
# Common Image Helpers #
########################

def get_image_spdxref(image_obj):
    '''Given the image object, return an SPDX reference ID'''
    # here we return the image name, tag and id
    return 'SPDXRef-{}'.format(image_obj.get_human_readable_id())


########################
# Common Layer Helpers #
########################

def get_file_licenses(filedata):
    '''Return a unique list of file licenses'''
    return list(set(filedata.licenses))


def get_layer_licenses(layer_obj):
    '''Return a list of unique licenses from the files analyzed
    in the layer object. It is assumed that the files were analyzed and
    there should be some license expressions. If there are not, an empty list
    is returned'''
    licenses = set()
    for filedata in layer_obj.files:
        # we will use the SPDX license expressions here as they will be
        # valid SPDX license identifiers
        if filedata.licenses:
            for lic in get_file_licenses(filedata):
                licenses.add(lic)
    return list(licenses)


def get_layer_spdxref(layer_obj):
    '''Given the layer object, return an SPDX reference ID'''
    # here we return the shortened diff_id of the layer
    return 'SPDXRef-{}'.format(layer_obj.diff_id[:10])


def get_layer_verification_code(layer_obj):
    '''Calculate the verification code from the files in an image layer. This
    assumes that layer_obj.files_analyzed is True. The implementation follows
    the algorithm in the SPDX spec v 2.1 which requires SHA1 to be used to
    calculate the checksums of the file and the final verification code'''
    sha1_list = []
    for filedata in layer_obj.files:
        filesha = filedata.get_checksum('sha1')
        if not filesha:
            # we cannot create a verification code, hence file generation
            # is aborted
            logger.critical(
                'File %s does not have a sha1 checksum. Failed to generate '
                'a SPDX tag-value report', filedata.path)
            return None
        sha1_list.append(filesha)
    sha1_list.sort()
    sha1s = ''.join(sha1_list)
    return hashlib.sha1(sha1s.encode('utf-8')).hexdigest()  # nosec


def get_layer_checksum(layer_obj):
    '''Return a SPDX formatted checksum value. It should be of the form:
    checksum_type: <checksum>'''
    return '{}: {}'.format(layer_obj.checksum_type.upper(), layer_obj.checksum)


##########################
# Common Package Helpers #
##########################

def get_package_spdxref(package_obj):
    '''Given the package object, return an SPDX reference ID'''
    return 'SPDXRef-{}'.format(
        spdx_formats.package_id.format(
            name=package_obj.name,
            ver=package_obj.version).replace(':', '-', 1))


#######################
# Common File Helpers #
#######################

def get_file_spdxref(filedata, layer_id):
    '''Given a FileData object, return a unique identifier for the SPDX
    document. According to the spec, this should be of the form: SPDXRef-<id>
    We will use a combination of the file name, checksum and layer_id and
    calculate a hash of this string'''
    file_string = filedata.path + filedata.checksum[:7] + layer_id
    fileid = get_string_id(file_string)
    return 'SPDXRef-{}'.format(fileid)


def get_file_checksum(filedata):
    '''Given a FileData object, return the checksum required by SPDX.
    This should be of the form: <checksum_type>: <checksum>
    Currently, the spec requires a SHA1 checksum'''
    return '{}: {}'.format('SHA1', filedata.get_checksum('sha1'))


def get_file_notice(filedata):
    '''Return a formatted string with all copyrights found in a file. Return
    an empty string if there are no copyrights'''
    notice = ''
    for cp in filedata.copyrights:
        notice = notice + cp + '\n'
    return notice


def get_file_comment(filedata):
    '''Return a formatted comment string with all file level notices. Return
    an empty string if no notices are present'''
    comment = ''
    for origin in filedata.origins.origins:
        comment = comment + '{}:'.format(origin.origin_str) + '\n'
        for notice in origin.notices:
            comment = comment + \
                '{}: {}'.format(notice.level, notice.message) + '\n'
    return comment
