# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
from git import GitCommandError
import os
import re
import sys

# This script is written to be used with CI Integration


def lint_commit(commit_id):
    """Given a commit ID, determine if the
    commit message complies with the tern guidelines. If
    it does not comply, output the offending commit and
    specify the reason for failure."""

    r = Repo(os.getcwd())
    check = True
    message = r.commit(commit_id).message
    sha_short = r.git.rev_parse(commit_id, short=7)

    # Check 1: Subject, body and DCO exist
    # Note that git does not allow for empty subjects
    if len(re.split('\n\n|\r', message)) <= 2:
        print("Commit {} does not have a body.".format(sha_short))
        check = False

    # Check 2: Subject length is less than about 50
    if len(re.split('\n\n', message)[0]) > 54:
        print(
            "The subject of commit {} should be 50 characters or less.".format(
                sha_short))
        check = False

    # Check 3: Each line of the body is less than 72
    msg_list = re.split('\n\n|\r', message)
    msg_list.pop(0)
    msg_list.pop()
    for msg in msg_list:
        for line in msg.split('\n'):
            if len(line) > 72:
                print("Line exceeds 72 characters.\n"
                      "Line: {0}\n"
                      "Commit: {1}\n\n".format(line, sha_short))
                check = False

    if check:
        print("Commit message checks pass")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    # Get the list of commits and loop through them,
    # inputting each one into the linting function

    # We are in the 'tern' directory
    repo = Repo(os.getcwd())
    try:
        repo.git.remote(
            'add', 'upstream', 'https://github.com/tern-tools/tern.git')
    except GitCommandError:
        pass
    repo.git.fetch('upstream')
    # Will return commit IDs differentiating HEAD and main
    commitstr = repo.git.rev_list('HEAD', '^upstream/main', no_merges=True)
    # If we are on the project's main branch then there will be no
    # difference and the result will be an empty string
    # So we will not proceed if there is no difference
    if commitstr:
        commits = commitstr.split('\n')
        for commit_id in commits:
            lint_commit(commit_id)
