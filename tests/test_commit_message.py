# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
import os
import re
import sys

check = True

# we are currently in the 'tern' repo
repo = Repo(os.getcwd())
commitmsg = repo.head.commit.message

message = re.split('\n\n|\r', commitmsg, 1)
body = re.split('\n|\r', message[1])

# Git does not allow for empty titles
# Check that commit message has 3 elements
# for title, body and signed-off line
if len(re.split('\n\n|\r', commitmsg)) <= 2:
    print("Commit message should have a body.")
    check = False

# Check subject length
if len(message[0]) > 54:
    print("Commit message subject should be 50 characters or less.")
    check = False

# Check body length 
for i in range(len(body)):
    if len(body[i]) > 72:
        print("Line {} of the body may not exceed 72 characters.".format(i+1))
        check = False

if not check:
    sys.exit(1)
