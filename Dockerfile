# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

FROM debian:buster

# Install fuse-overlayfs and Tern dependencies
RUN apt-get update && apt-get -y install wget gnupg2 tar findutils attr util-linux python3 python3-pip python3-setuptools git && pip3 install --upgrade pip && pip3 install tern && echo 'deb http://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/Debian_10/ /' > /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list && wget -nv https://download.opensuse.org/repositories/devel:kubic:libcontainers:stable/Debian_10/Release.key -O Release.key && apt-key add - < Release.key && apt-get update -qq && apt-get -qq -y install buildah fuse-overlayfs && rm -rf /var/cache /var/log/dnf* /var/log/yum.*

# Adjust storage.conf to enable Fuse storage.
RUN sed -i -e 's|^#mount_program|mount_program|g' -e '/additionalimage.*/a "/var/lib/shared",' /etc/containers/storage.conf

ENTRYPOINT ["tern", "--driver", "fuse"]
CMD ["-h"]
