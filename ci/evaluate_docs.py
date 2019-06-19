# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
import os
import subprocess  # nosec
import sys


# Run lint tests only for .py files

prospector = "prospector {}"

repo = Repo(os.getcwd())
repo.git.remote('add', 'upstream', 'git@github.com:vmware/tern.git')
repo.git.fetch('upstream')

hcommit = repo.head.commit
diff = hcommit.diff('upstream/master')

changes = []
for d in diff:
    # Get the list of strings for changed files
    changes.append(d.b_path)

# check that changes has entries
if not changes:
    print('No changes to lint.')
    sys.exit(0)

for change in changes:
    if change[-3:] == '.py':
        pipes = subprocess.Popen(  # nosec
            prospector.format(change), shell=True, stdout=subprocess.STDOUT,
            stderr=subprocess.STDOUT)
        pipes.communicate()  # nosec
