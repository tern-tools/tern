# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Patrick Dwyer. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

'''
Helper functions for packages in CycloneDX JSON document creation
'''

from tern.formats.cyclonedx import cyclonedx_common
from packageurl import PackageURL


def get_package_dict(os_guess, package):
    ''' Given a package format, namespace and package object return a
    CycloneDX JSON dictionary representation of the package. '''
    package_dict = {
        'name': package.name,
        'version': package.version,
        'type': 'application',
    }

    purl_type = package.pkg_format
    purl_namespace = cyclonedx_common.get_purl_namespace(os_guess, package.pkg_format)
    if purl_type:
        purl = PackageURL(purl_type, purl_namespace, package.name, package.version)
        package_dict['purl'] = str(purl)

    if package.pkg_license:
        package_dict['licenses'] = [cyclonedx_common.get_license_from_name(package.pkg_license)]

    if package.pkg_licenses:
        package_dict['evidence'] = {'licenses': []}
        for pkg_license in package.pkg_licenses:
            package_dict['evidence']['licenses'].append(cyclonedx_common.get_license_from_name(pkg_license))

    return package_dict


def get_packages_list(image_obj):
    ''' Given an image object return a list of CycloneDX dictionary
    representations for each of the packages in the image '''
    package_dicts = []

    os_guess = cyclonedx_common.get_os_guess(image_obj)

    for layer_obj in image_obj.layers:
        for package in layer_obj.packages:
            package_dicts.append(get_package_dict(os_guess, package))

    return package_dicts
