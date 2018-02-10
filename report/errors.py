'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

'''
Error messages
'''

no_packages = '''Unable to recover packages for layer {layer_id}. Consider ''' \
    '''either entering them manually or create a bash script to retrieve ''' \
    '''the package in the command library.\n'''
no_version = '''No version for package {package_name}. Consider either ''' \
    '''entering the version manually or creating a script to retrieve ''' \
    '''it in the command library\n'''
no_license = '''No license for package {package_name}. Consider either ''' \
    '''entering the license manually or creating a script to retrieve it ''' \
    '''in the command library\n'''
no_src_url = '''No source url for package {package_name}. Consider either ''' \
    '''entering the source url manually or creating a script to retrieve ''' \
    '''it in the command library\n'''
env_dep_dockerfile = '''Docker build failed: {build_fail_msg} \n Since ''' \
    '''the Docker image cannot be built, Tern will try to retrieve ''' \
    '''package information from the Dockerfile itself.\n'''
no_listing_for_base_key = '''No listing for key {listing_key}. ''' \
    '''Consider adding this listing to command_lib/base.yml.\n'''
no_listing_for_package_key = '''No listing for key {listing_key}. ''' \
    '''Consider adding this listing to command_lib/snippets.yml.\n'''
unsupported_listing_for_key = '''Unsupported listing for key ''' \
    '''{listing_key}.\n'''
