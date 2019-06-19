# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
import os

# This is meant to run within circleci
# Print out only .py files that have changed
# Pipe to any linting tools

repo = Repo(os.getcwd())
repo.git.remote('add', 'upstream', 'git@github.com:vmware/tern.git')
repo.git.fetch('upstream')

hcommit = repo.head.commit
diff = hcommit.diff('upstream/master')

if not diff:
    print('No changes to lint.')

for d in diff:
    if os.path.exists(d.b_path) and (d.b_path)[-3:] == '.py':
        print(d.b_path)
