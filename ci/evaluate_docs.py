# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
from git import GitCommandError
import os
import sys
import subprocess

# This is meant to run within CI Integration
# Print out only .py files that have changed
# Pipe to any linting tools
# Note that some linting tools will lint everything if the output
# of this script is nothing

output = subprocess.check_output(['git', 'remote', '-v'])
print(output.decode('utf-8'))

repo = Repo(os.getcwd())
try:
    repo.git.remote('add', 'upstream', 'https://github.com/vmware/tern.git')
except GitCommandError:
    pass
repo.git.fetch('upstream')

hcommit = repo.head.commit
diff = hcommit.diff('upstream/master')

if not diff:
    sys.exit(0)

for d in diff:
    if os.path.exists(d.b_path) and (d.b_path)[-3:] == '.py':
        print(d.b_path)
