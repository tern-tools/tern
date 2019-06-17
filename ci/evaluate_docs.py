# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
import os
import sys


# This script is designed to be run with circleci.
# This script should pass if we need to run Bandit and Prospector,
# which means that there are files other than *.md files being changed.
# If only *.md files are changed, we don't need to run Bandit
# or Prospector and the script will fail.

# Assume that all files are *.md until proven otherwise
docs_only = True


repo = Repo(os.getcwd())
repo.git.remote('add', 'upstream', 'git@github.com:vmware/tern.git')
repo.git.fetch('upstream')

hcommit = repo.head.commit
diff = hcommit.diff('upstream/master')

changes=[]
for d in diff:
    # Get the list of strings for changed files
    changes.append(d.b_path)

# check that changes has entries
if not changes:
    print('No changes to run tests for.')
    sys.exit(0)

for change in changes:
    if change[-3:] != '.md':
        docs_only = False
        break

if docs_only:
    sys.exit(1)
else:
    sys.exit(0)
