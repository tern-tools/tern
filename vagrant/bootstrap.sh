#!/usr/bin/env bash


# Update the Ubuntu repositories
sudo apt-get update

# Upgrade all currently installed packages
sudo apt-get -y upgrade

# Python3 versions and system dependencies
sudo apt-get install -y python3 python3-pip python3-venv attr

# Install Docker
sudo apt-get install -y docker.io

# Docker adjustments

# Optional: Make it easier to run Docker commands by adding
# the vagrant user to the Docker group. If you want to run commands
# against Docker without doing this, you will need to use sudo.

sudo usermod -a -G docker vagrant

# Install dependencies
cd /tern
pip3 install -r requirements.txt
