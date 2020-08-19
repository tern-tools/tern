# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

'''
Constants
'''

# paths for working on container images
# this is relative to the user's home directory

# hidden folder
dot_folder = '.tern'
# working folder
temp_folder = 'temp'
# temporary tar file
temp_tarfile = 'temp.tar'
# built image name
image = 'ternimage'
# built image tag
tag = 'terntag'
# running container name
container = 'terncontainer'
# logger name
logger_name = 'ternlog'
# logfile
logfile = 'tern.log'
# manifest file
manifest_file = 'manifest.json'
# cache file
cache_file = 'cache.json'
# default shell
shell = '/bin/sh'
# path where resolv.conf lives
resolv_path = '/etc/resolv.conf'
# paths where os-release could be
etc_release_path = 'etc/os-release'
lib_release_path = 'usr/lib/os-release'
# directory where layer.tar can be extracted to
untar_dir = 'contents'
# rootfs working directory
# this is relative to where tern is
workdir = 'workdir'
# rootfs directory where overlay merges filesystems
# this is relative to where tern is
mergedir = 'mergedir'
# locked dockerfile
locked_dockerfile = 'Dockerfile.lock'
# temporary directory for multistage Dockerfile analysis
multistage_dir = 'dftemp'
