FROM mcr.microsoft.com/vscode/devcontainers/python:3.9

RUN apt-get update \
  && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y --no-install-recommends install \
  attr \
  # Require a more recent version of fuse-overlayfs
  && echo 'deb http://deb.debian.org/debian unstable main' >> /etc/apt/sources.list \
  && apt-get update \
  && apt-get -y --no-install-recommends install \
  fuse-overlayfs \
  && rm -rf /var/lib/apt/lists/*