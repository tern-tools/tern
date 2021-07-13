# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Patrick Dwyer. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

'''
Helper functions for image level JSON CycloneDX document dictionaries
'''


from tern.formats.cyclonedx import cyclonedx_common
from packageurl import PackageURL


def get_image_dict(image_obj):
    ''' Given an image object return the CycloneDX document dictionary for the
    given image. For CycloneDX, the image is a component and hence follows the
    JSON spec for components. '''
    image_dict = {
        'type': 'container',
        'scope': 'required',
        'name': image_obj.name,
        'version': image_obj.checksum_type + ':' + image_obj.checksum,
        'hashes': [],
        'properties': []
    }

    purl = PackageURL('docker', None, image_dict['name'], image_dict['version'])
    image_dict['purl'] = str(purl)

    if image_obj.repotags:
        for repotag in image_obj.repotags:
            image_dict['properties'].append(cyclonedx_common.get_property('tern:repotag', repotag))

    os_guess = cyclonedx_common.get_os_guess(image_obj)
    if os_guess:
        image_dict['properties'].append(cyclonedx_common.get_property('tern:os_guess', os_guess))

    cdx_hash = cyclonedx_common.get_hash(image_obj.checksum_type, image_obj.checksum)
    if cdx_hash is not None:
        image_dict['hashes'].append(cdx_hash)

    return image_dict
