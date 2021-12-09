#!/usr/bin/env bash
#
# Copyright (c) 2018-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

# Update the Ubuntu repositories
sudo apt-get update

# Upgrade all currently installed packages
sudo apt-get -y upgrade

# Python3 versions and system dependencies
sudo apt-get install -y python3 python3-pip python3-venv attr jq

# Install skopeo for Ubuntu 20.04
echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_20.04/ /" | sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list
curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/xUbuntu_20.04/Release.key | sudo apt-key add -
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install skopeo

# Install Docker
sudo apt-get install -y docker.io

# Docker adjustments

# Optional: Make it easier to run Docker commands by adding
# the vagrant user to the Docker group. If you want to run commands
# against Docker without doing this, you will need to use sudo.

sudo usermod -a -G docker vagrant

# Install tern
pip3 install tern
