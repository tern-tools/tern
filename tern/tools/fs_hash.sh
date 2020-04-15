#!/bin/sh
#
# Copyright (c) 2018-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
# Given a file path, create a list of file stats and their sha256sums
# usage: ./fs_hash.sh path/to/dir
# format:
# permissions|uid|gid|size in bytes|number of hard links| sha256sum filepath
# extended attributes list
#
# repeat for each file
#
# Check that all commands to collect metadata exist on the
# system otherwise exit.

command -v find || { echo "'find' not found on system." >&2 ; exit 1; }
command -v sha256sum || { echo "'sha256sum' not found on system." >&2 ; exit 1; }
command -v getfattr || { echo "'getfattr' not found on system." >&2 ; exit 1; }

cwd=`pwd`
cd $1
find -type f ! -size 0 -printf "%M|%U|%G|%s|%n|" -exec sha256sum {} \; -exec getfattr -d -m - {} \;
cd $cwd
