#!/bin/sh
#
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
# Given a file path, create a list of file stats and their sha256sums
# usage: ./fs_hash.sh path/to/dir
# format: inode|permissions|uid|gid|size in bytes|number of hard links|security context|sha256sum filepath

pushd $1 > /dev/null;
  find -type f -printf "%i|%M|%U|%G|%s|%n|%Z|" -exec sha256sum {} \;
popd > /dev/null;
