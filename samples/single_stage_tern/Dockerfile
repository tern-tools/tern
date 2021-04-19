# Copyright (c) 2019-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

FROM debian:buster

# Install fuse-overlayfs and Tern dependencies
RUN apt-get update && \
    apt-get -y install \
    attr \
    findutils \
    git \
    gnupg2 \
    jq \
    python3 \
    python3-pip \
    python3-setuptools \
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

# Install tern
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir \
    tern

ENTRYPOINT ["tern", "--driver", "fuse"]
CMD ["-h"]
