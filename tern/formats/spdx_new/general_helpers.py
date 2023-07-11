# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
General helpers for SPDX document generator
"""
import hashlib
import re
import uuid
from datetime import datetime
from typing import Union, Tuple

from license_expression import get_spdx_licensing, LicenseExpression, Licensing
from spdx_tools.spdx.model import SpdxNone

from tern.classes.file_data import FileData
from tern.classes.image import Image
from tern.classes.image_layer import ImageLayer
from tern.classes.package import Package


def get_uuid() -> str:
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def get_string_id(string: str) -> str:
    """Return a unique identifier for the given string"""
    return hashlib.sha256(string.encode('utf-8')).hexdigest()[-7:]


def get_license_ref(license_string: str) -> str:
    """For SPDX format, return a LicenseRef string"""
    return 'LicenseRef-' + get_string_id(str(license_string))


def replace_invalid_chars_in_license_expression(license_string: str) -> str:
    """Given a license string, replace common invalid SPDX license characters."""
    not_allowed = [',', ';', '/', '&']
    if any(x in license_string for x in not_allowed):
        # Try to replace common invalid license characters
        license_string = license_string.replace(',', ' and')
        license_string = license_string.replace('/', '-')
        license_string = license_string.replace(';', '.')
        license_string = license_string.replace('&', 'and')
    return license_string


def is_valid_license_expression(license_string: str) -> bool:
    licensing = get_spdx_licensing()
    try:
        return licensing.validate(license_string).errors == []
    # Catch any invalid license chars here
    except AttributeError:
        return False


def get_package_license_declared(package_license_declared: str) -> Union[LicenseExpression, SpdxNone]:
    """After substituting common invalid SPDX license characters using
    the is_spdx_license_expression() function, determines if the declared
    license string for a package or file is a valid SPDX license expression.
    If license expression is valid after substitutions, return the updated string.
    If not, return the LicenseRef of the original declared license expression
    passed in to the function. If a blank string is passed in, return `NONE`."""
    if package_license_declared:
        package_license_declared = replace_invalid_chars_in_license_expression(package_license_declared)
        if is_valid_license_expression(package_license_declared):
            return Licensing().parse(package_license_declared)

        return Licensing().parse(get_license_ref(package_license_declared))
    return SpdxNone()


###########################################################################################
# central place for SPDXRef-generators to avoid circular imports as these are widely used #
###########################################################################################

def get_image_spdxref(image_obj: Image) -> str:
    """Given the image object, return an SPDX reference ID"""
    # here we return the image name, tag and id
    return f'SPDXRef-{image_obj.get_human_readable_id()}'


def get_package_spdxref(package_obj: Package) -> Tuple[str, str]:
    """Given the package obj, return an SPDX reference ID for the binary
    and source package, if available"""
    pkg_ref = f"{package_obj.name}-{package_obj.version}"
    src_ref = ''
    if package_obj.src_name:
        # differentiate between binary and source package refs
        src_ver = package_obj.src_version + "-src"
        src_ref = f"{package_obj.src_name}-{src_ver}"
    # replace all the strings that SPDX doesn't like
    # allowed characters are: letters, numbers, "." and "-"
    clean_pkg_ref = re.sub(r'[:+~_/]', r'-', pkg_ref)
    if src_ref:
        clean_src_ref = re.sub(r'[:+~/]', r'-', src_ref)
        return f'SPDXRef-{clean_pkg_ref}', f'SPDXRef-{clean_src_ref}'
    return f'SPDXRef-{clean_pkg_ref}', ''


def get_layer_spdxref(layer_obj: ImageLayer) -> str:
    """Given the layer object, return an SPDX reference ID"""
    # here we return the shortened diff_id of the layer
    return f'SPDXRef-{layer_obj.diff_id[:10]}'


def get_file_spdxref(filedata: FileData, layer_id: str) -> str:
    """Given a FileData object, return a unique identifier for the SPDX
    document. According to the spec, this should be of the form: SPDXRef-<id>
    We will use a combination of the file name, checksum and layer_id and
    calculate a hash of this string"""
    file_string = filedata.path + filedata.checksum[:7] + layer_id
    fileid = get_string_id(file_string)
    return f'SPDXRef-{fileid}'
