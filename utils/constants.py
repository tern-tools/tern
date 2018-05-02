'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

'''
Constants
'''

# temporary folder for extracting container image
# this is relative to where the tern executable is
temp_folder = 'temp'
# built image name
image = 'testimage'
# built image tag
tag = 'testtag'
# running container name
container = 'testcontainer'
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
# rootfs working directory
# this is relative to where tern is
workdir = 'workdir'
# rootfs directory where layer diff filesystem is extracted
# this is relative to where tern is
upperdir = 'updir'
# report file
report_file = 'report.txt'
