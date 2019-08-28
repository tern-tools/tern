# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

FROM photon:3.0

# install system dependencies
# photon:3.0 comes with toybox which conflicts with some dependencies needed for tern to work, so uninstalling
# toybox first
RUN tdnf remove -y toybox && tdnf install -y findutils attr util-linux python3 python3-pip python3-setuptools git

# copy tern repo into root
COPY . tern

# install app dependencies
RUN pip3 install --upgrade pip && pip3 install ./tern

# make a mounting directory
RUN mkdir temp

ENTRYPOINT ["tern", "-b"]
CMD ["-h"]
