# Copyright (c) 2017 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

#!/bin/bash
# Get sources for a list of packages

apt-get update
mkdir apt_sources
pushd apt_sources
  for package in "$@"
  do
    mkdir $package
    pushd $package
      apt-get source -d $package
    popd
  done
popd
tar cvzf apt_sources.tar.gz /apt_sources/*
