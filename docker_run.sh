#!/bin/sh
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
# Script to run Tern within a prebuilt Docker container
# Assume the Tern Docker container exists on the host
# The script will make a directory that you provide
# It will then run a docker container in privileged mode and bind mount to the directory
#
# Usage: ./docker_run.sh <tern image> <tern command arguments in quotes> > output.txt
# Example: ./docker_run.sh ternd "report -i golang:alpine" > output.txt

docker run --privileged --device /dev/fuse -v /var/run/docker.sock:/var/run/docker.sock --rm $1 $2
