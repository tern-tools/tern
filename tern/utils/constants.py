# -*- coding: utf-8 -*-
#
# Copyright (c) 2017, 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

'''
Constants
'''

# temporary folder for extracting container image
# this is relative to where the tern executable is
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
cache_file = 'cache.yml'
# default shell
shell = '/bin/sh'
# path where resolv.conf lives
resolv_path = '/etc/resolv.conf'
# directory where layer.tar can be extracted to
untar_dir = 'contents'
# rootfs working directory
# this is relative to where tern is
workdir = 'workdir'
# rootfs directory where overlay merges filesystems
# this is relative to where tern is
mergedir = 'mergedir'
# report file
report_file = 'report.txt'
yaml_file = 'report.yml'
json_file = 'report.json'
