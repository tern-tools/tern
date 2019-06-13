# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
import os
import re
import sys

# This script is written to be used with circleci and
# is not meant to be run locally


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
    body = re.split('\n\n|\r', message, 1)[1]
    for i in range(len(body)):
        if len(body[i]) > 72:
            print("Line {0} of commit {1} exceeds 72 characters.".format(
                i+1, sha_short))
            check = False

    if not check:
        sys.exit(1)


if __name__ == '__main__':
    # Get the list of commits and loop through them,
    # inputting each one into the linting function

    # We are in the 'tern' directory
    repo = Repo(os.getcwd())
    repo.git.remote('add', 'upstream', 'git@github.com:vmware/tern.git')
    repo.git.fetch('upstream')
    # Will return commit IDs differentiating HEAD and master
    commitstr = repo.git.rev_list('HEAD', '^upstream/master')
    # If we are on the main project's master branch then there will be no
    # difference and the result will be an empty string
    # So we will not proceed if there is no difference
    if commitstr:
        commits = commitstr.split('\n')
        for commit_id in commits:
            lint_commit(commit_id)
