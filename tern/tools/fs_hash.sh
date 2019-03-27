#!/bin/sh
#
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
# Given a file path, create a list of file stats and their sha256sums
# usage: ./fs_hash.sh path/to/dir
# format:
# permissions|uid|gid|size in bytes|number of hard links| sha256sum filepath
# extended attributes list
#
# repeat for each file

cwd=`pwd`
cd $1
find -type f -printf "%M|%U|%G|%s|%n|" -exec sha256sum {} \; -exec getfattr -d -m - {} \;
cd $cwd
