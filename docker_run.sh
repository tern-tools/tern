#!/bin/sh
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
# Script to run Tern within a prebuilt Docker container
# Assume the Tern Docker container exists on the host
# The script will make a directory that you provide
# It will then run a docker container in privileged mode and bind mount to the directory
#
# Usage: ./docker_run.sh <directory_name> <tern image> <tern command arguments in quotes>
# Example: ./docker_run.sh workdir ternd "report -i golang:alpine"

mkdir -p $1
docker run --privileged -v /var/run/docker.sock:/var/run/docker.sock --mount type=bind,source=$PWD/$1,target=/hostmount --rm $2 $3
