# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Error messages
"""

unrecognized_base = '''Unable to determine the base OS of the image ''' \
    '''{image_name}:{image_tag}\n'''
no_packages = '''Unable to recover packages for layer {layer_id}. ''' \
    '''Consider either entering them manually or create a bash script to ''' \
    '''retrieve the package in the command library.\n'''
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
no_listing_for_snippet_key = '''No listing for key {listing_key}. ''' \
    '''Consider adding this listing to command_lib/snippets.yml.\n'''
unsupported_listing_for_key = '''Unsupported listing for key ''' \
    '''{listing_key}.\n'''
cannot_retrieve_base_packages = '''Cannot retrieve the packages in the ''' \
    '''base image {image}:{tag}. Check the command listing in the command ''' \
    '''library'''
no_invocation = '''No invocation steps to perform within a container nor ''' \
    '''on the host machine.\n To tell the tool how to retrieve this ''' \
    '''information, make an entry in command_lib/base.yml'''
no_image_tag_listing = '''No listing of {image_name}:{image_tag} in the '''\
    '''command library. To add one, make an entry in command_lib/base.yml'''
no_command_listing = '''No listing of hardcoded or retrieval steps for ''' \
    '''{command_name} nor any default listing.\n To tell the tool this ''' \
    '''information make an entry in command_lib/snippets.yml\n'''
incomplete_command_lib_listing = '''The command library has an incomplete ''' \
    '''listing for {image_name}:{image_tag}. Please complete the listing ''' \
    '''based on the examples.\n'''
no_shell_listing = '''There is no listing for 'shell' under the base ''' \
    '''listing for {binary}. Using default shell: ''' \
    '''{default_shell}\n'''
unknown_content = '''Unknown content included in layer {files}. Please ''' \
    '''analyze these files separately\n'''

# Dockerfile specific errors
dockerfile_no_tag = '''The Dockerfile provided has no tag in the line ''' \
    '''{dockerfile_line}. Consider using a specific immutable tag. ''' \
    '''Defaulting to 'latest'...\n'''
dockerfile_using_latest = '''The Dockerfile is using the tag 'latest' ''' \
    '''in line {dockerfile_line}. Consider using a specific immutable tag'''
cannot_parse_base_image = '''Unable to parse base image in the Dockerfile ''' \
    '''{dockerfile}. Error: {error_msg}\n'''
base_image_not_found = '''Failed to pull the base image. Perhaps it was ''' \
    '''removed from Dockerhub\n'''
cannot_extract_base_image = '''Failed to extact base image {image}:{tag}.'''
docker_build_failed = '''Unable to build docker image using Dockerfile ''' \
    '''{dockerfile}: {error_msg}\n'''
docker_tag_fallback = '''Falling back on tag {latest_tag} in ''' \
    '''command_lib/base.yml under {image} listing.\n'''
dockerfile_fallback = '''Falling back on parsing the Dockerfile for ''' \
    '''package information\n'''
no_running_docker_container = '''Cannot invoke commands in a container '''\
    '''as there is no running container.\n'''
cannot_find_image = '''Cannot find image {imagetag} locally or from remote '''\
    '''registry.\n'''

# not error messages but stuff for the logger
no_base_image = '''Base image is FROM scratch. Skipping to build'''
