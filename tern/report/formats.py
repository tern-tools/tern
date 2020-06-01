# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Report formatting for different types of reports and report content
"""


# formatting variables
layer_id = ''
package_name = ''
package_version = ''
package_url = ''
package_license = ''
package_info_retrieval_errors = ''
package_info_reporting_improvements = ''

# general formatting
# report disclaimer
disclaimer = '''This report was generated by the Tern Project\n''' \
    '''{version_info}\n\n'''
disclaimer_yaml = '''# This report was generated by the Tern Project\n''' \
    '''# {version_info}\n\n'''

commit_version = "https://github.com/tern-tools/tern/commit/{commit_sha}"
packaged_version = "Version: {version}"

# cache
retrieve_from_cache = '''Retrieving packages from cache for layer ''' \
    '''{layer_id}:\n\n'''
# command library
base_listing = '''Direct listing in command_lib/base.yml'''
snippet_listing = '''Direct listing in command_lib/snippets.yml'''
invoke_for_base = '''Retrieved by invoking listing in command_lib/base.yml'''
invoke_for_snippets = '''Retrieved by invoking listing in command_lib/''' \
    '''snippets.yml'''
invoke_in_container = '''\tin container:\n'''
invoke_on_host = '''\ton host:\n'''
# package information
package_name = '''Package: {package_name}\n'''
package_version = '''Version: {package_version}\n'''
package_url = '''Project URL: {package_url}\n'''
package_license = '''License: {package_license}\n'''
package_copyright = '''Copyright Text: {package_copyright}\n'''
layer_packages_list = '''\tPackages found in Layer:  {list}\n'''
layer_licenses_list = '''\tLicenses found in Layer:  {list}\n'''
layer_file_licenses_list = '''\tFile licenses found in Layer:  {list}\n'''
full_licenses_list = '''###########################################\n'''\
    '''# Summary of licenses found in Container: #\n'''\
    '''###########################################\n{list}\n'''

# notes
package_notes = '''Errors: {package_info_retrieval_errors}\n''' \
    '''Improvements: {package_info_reporting_improvements}\n'''
# demarkation
package_demarkation = '''------------------------------------------------''' \
    '''\n\n'''

# informational
loading_from_cache = '''Loading packages from cache for layer {layer_id}'''
invoking_base_commands = '''Invoking commands from command_lib/base.yml'''
invoking_snippet_commands = '''Invoking commands from ''' \
    '''command_lib/snippets.yml'''
ignored = '''\nIgnored Commands:'''
unrecognized = '''\nUnrecognized Commands:'''
os_style_guess = '''Found {package_manager} package manager with '''\
    '''{package_format} package format. Possible OS(es) for this layer '''\
    '''might be: {os_list}'''
os_release = '''Found '{os_style}' in /etc/os-release.'''

# report formatting for dockerfiles

# dockerfile variables
base_image_instructions = ''
dockerfile_instruction = ''

# dockerfile report sections
dockerfile_image = '''Image built from Dockerfile {dockerfile}'''
dockerfile_base = '''Base Image: {base_image_instructions}'''
dockerfile_line = '''Instruction Line: {dockerfile_instruction}'''
oci_image_line = '''Instruction Line: {oci_image_instruction}'''
image_build_failure = '''Failed to build image from Dockerfile'''
image_load_failure = '''Failed to load metadata for built image {testimage}'''
layer_created_by = '''Layer created by commands: {created_by}'''
no_created_by = '''No information about filesystem creation'''

# docker image report
docker_image = '''Docker image: {imagetag}'''
# OCI image report
oci_image = '''OCI image: {imagetag}'''

# format for notices
notice_format = '''{origin}:\n\t{info}\n\twarnings:{warnings}''' \
    '''\n\terrors:{errors}\n\thints:{hints}\n'''
