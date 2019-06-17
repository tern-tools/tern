# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
import os
import re
import sys
import subprocess  # nosec


# This script is written to be used with circleci

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
    print('No changes to run tests for.')
    sys.exit(0)

test_suite = {
    # dev-requirements.txt
    re.compile('dev-requirements.txt'): ['tern -l report -i photon:3.0'],
    # requirements.txt
    re.compile('requirements.txt'): ['tern -l report -i photon:3.0'],
    # Dockerfile
    re.compile('Dockerfile'): [
        'docker build -t ternd .',
        './docker_run.sh workdir ternd "report -i golang:alpine"'],
    # Files under tern directory
    re.compile('tern/__init__.py|tern/__main__.py'):
    ['tern -l report -i golang:alpine'],
    # tern/classes
    re.compile('tern/classes/command.py'):
    ['python tests/test_class_command.py'],
    re.compile('tern/classes/docker_image.py'):
    ['python tests/test_class_docker_image.py'],
    re.compile('tern/classes/image.py'):
    ['python tests/test_class_image.py'],
    re.compile('tern/classes/image_layer.py'):
    ['python tests/test_class_image_layer.py'],
    re.compile('tern/classes/notice.py'):
    ['python tests/test_class_notice.py'],
    re.compile('tern/classes/notice_origin.py'):
    ['python tests/test_class_notice_origin.py'],
    re.compile('tern/classes/origins.py'):
    ['python tests/test_class_origins.py'],
    re.compile('tern/classes/package.py'):
    ['python tests/test_class_package.py'],
    re.compile('tern/classes/template.py'):
    ['python tests/test_class_template.py'],
    # tern/command_lib
    re.compile('tern/command_lib'): [
        'tern -l report -i photon:3.0',
        'tern -l report -i debian:buster',
        'tern -l report -i alpine:3.9',
        'tern -l report -i archlinux:latest',
        'tern -l report -i centos:7'],
    # tern/helpers
    re.compile('tern/helpers'): [
        'tern -l report -i golang:alpine',
        'tern -l report -d samples/alpine_python/Dockerfile'],
    # tern/report
    re.compile('tern/report'): [
        'tern -l report -i golang:alpine',
        'tern -l report -j photon:3.0',
        'tern -l report -y -i photon:3.0',
        'tern -l report -s -i photon:3.0',
        'tern -l report -m spdxtagvalue -i photon:3.0',
        'tern -l report -d samples/alpine_python/Dockerfile'],
    # tern/tools
    re.compile('tern/tools'):
    ['tern -l report -i golang:alpine'],
    # tern/utils
    re.compile('tern/utils'): [
        'tern -l report -i golang:alpine',
        'tern -l report -d samples/alpine_python/Dockerfile'],
    # tests
    re.compile('tests/test_class_command.py'):
        ['python tests/test_class_command.py'],
    re.compile('tests/test_class_docker_image.py'):
        ['python tests/test_class_docker_image.py'],
    re.compile('tests/test_class_image.py'):
        ['python tests/test_class_image.py'],
    re.compile('tests/test_class_image_layer.py'):
        ['python tests/test_class_image_layer.py'],
    re.compile('tests/test_class_notice.py'):
        ['python tests/test_class_notice.py'],
    re.compile('tests/test_class_notice_origin.py'):
        ['python tests/test_class_notice_origin.py'],
    re.compile('tests/test_class_origins.py'):
        ['python tests/test_class_origins.py'],
    re.compile('tests/test_class_package.py'):
        ['python tests/test_class_package.py'],
    re.compile('tests/test_class_template.py'):
        ['python tests/test_class_template.py']
        }

alltests = []
for change in changes:
    for check in test_suite.keys():
        if check.match(change):
            alltests.extend(test_suite[check])

# Remove duplicate tests
tests = list(set(alltests))

if not tests:
    print('No tests to run.')
else:
    print('Running the following tests:')
    for t in tests:
        print(t)
    print('-------------------------OUTPUT-------------------------')

# Run the tests -- Precaution will be mad!
for t in tests:
    subprocess.check_output(t, shell=True)  # nosec
