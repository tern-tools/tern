# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
# Build the Docker image:
#   docker build --tag tern .
# Run tern on its own Docker image:
#   docker run --rm --privileged --device /dev/fuse --volume /var/run/docker.sock:/var/run/docker.sock tern report --docker-image tern:latest

FROM python:3.7-slim

# Install fuse-overlayfs and Tern dependencies.
RUN apt-get update && \
    apt-get -y install \
        attr \
        findutils \
        git \
        gnupg2 \
        tar \
        util-linux \
        wget && \
    echo 'deb http://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/Debian_10/ /' > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list && \
    wget --no-verbose https://download.opensuse.org/repositories/devel:kubic:libcontainers:stable/Debian_10/Release.key -O - | apt-key add - && \
    apt-get update && \
    apt-get -y install \
        buildah \
        fuse-overlayfs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Adjust storage.conf to enable Fuse storage.
RUN sed -i -e 's|^#mount_program|mount_program|g' -e '/additionalimage.*/a "/var/lib/shared",' /etc/containers/storage.conf

# Install Tern.
WORKDIR /opt/tern
COPY . .
RUN python -m pip install --no-cache-dir --editable .

ENTRYPOINT ["tern", "--driver", "fuse"]
CMD ["-h"]
