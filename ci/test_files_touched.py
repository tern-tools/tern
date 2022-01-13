# -*- coding: utf-8 -*-
#
# Copyright (c) 2019-2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from git import Repo
from git import GitCommandError
import os
import re
import sys
import subprocess  # nosec


# This script is written to be used with CI integration

repo = Repo(os.getcwd())
try:
    repo.git.remote('add', 'upstream',
                    'https://github.com/tern-tools/tern.git')
except GitCommandError:
    pass
repo.git.fetch('upstream')

hcommit = repo.head.commit
diff = hcommit.diff('upstream/main')

changes = []
for d in diff:
    # Get the list of strings for changed files
    changes.append(d.b_path)

# check that changes has entries
if not changes:
    print('No changes to run tests for.')
    sys.exit(0)

test_suite = {
    # requirements.txt
    re.compile('requirements.txt'): ['tern report -i photon:3.0'],
    # Dockerfile
    re.compile('docker/Dockerfile'): [
        'python3 setup.py sdist && '
        'docker build -t ternd -f ci/Dockerfile . && '
        './docker_run.sh ternd "report -i golang:alpine"'],
    # Files under tern directory
    re.compile('tern/__init__.py|tern/__main__.py'):
    ['tern  report -i golang:alpine'],
    # tern/classes
    re.compile('tern/classes/command.py'):
    ['python tests/test_class_command.py'],
    re.compile('tern/classes/oci_image.py'):
    ['tern report -i photon:3.0',
     'python tests/test_class_oci_image.py'],
    re.compile('tern/classes/docker_image.py'):
    ['tern report -d samples/alpine_python/Dockerfile',
     'python tests/test_class_docker_image.py'],
    re.compile('tern/classes/file_data.py'):
    ['python tests/test_class_file_data.py'],
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
    ['python tests/test_class_template.py',
     'tern report -f spdxtagvalue -i photon:3.0',
     'tern lock samples/single_stage_tern/Dockerfile'],
    # tern/command_lib
    re.compile('tern/analyze/default/command_lib'): [
        'tern report -i photon:3.0',
        'tern report -i debian:buster',
        'tern report -i alpine:3.9',
        'tern report -i archlinux:latest',
        'tern report -i centos:7',
        'tern report -i node:12.16-alpine'],
    # tern/analyze/default/dockerfile
    re.compile('tern/analyze/default/dockerfile'): [
        'python tests/test_analyze_default_dockerfile_parse.py',
        'python tests/test_analyze_common.py',
        'tern report -i golang:alpine',
        'tern report -d samples/alpine_python/Dockerfile',
        'tern report -w photon.tar',
        'tern lock samples/single_stage_tern/Dockerfile'],
    # tern/load
    re.compile('tern/load'): [
        'python tests/test_load_docker_api.py'],
    # tern/report
    re.compile('tern/report'): [
        'tern report -i golang:alpine',
        'tern report -f yaml -i photon:3.0',
        'tern report -f json -i photon:3.0',
        'tern report -f spdxtagvalue -i photon:3.0',
        'tern report -f spdxjson -i photon:3.0',
        'tern report -d samples/alpine_python/Dockerfile',
        'tern report -f html -i photon:3.0',
        'tern report -f cyclonedxjson -i photon:3.0'],
    # tern/formats/spdx
    re.compile('tern/formats/spdx'): [
        'tern report -f spdxtagvalue -i photon:3.0 -o spdx.spdx && ' \
        'java -jar tools-java/target/tools-java-*-jar-with-dependencies.jar '\
        'Verify spdx.spdx',
        'tern report -f spdxjson -i photon:3.0 -o spdx.json && ' \
        'java -jar tools-java/target/tools-java-*-jar-with-dependencies.jar '\
        'Verify spdx.json'],
    # tern/tools
    re.compile('tern/tools'):
    ['tern report -i golang:alpine'],
    # tern/utils
    re.compile('tern/utils'): [
        'python tests/test_util_general.py',
        'tern report -i golang:alpine',
        'tern report -d samples/alpine_python/Dockerfile'],
    # tests
    re.compile('tests/test_analyze_common.py'):
        ['python tests/test_analyze_common.py'],
    re.compile('tests/test_analyze_default_filter.py'):
        ['python tests/test_analyze_default_filter.py'],
    re.compile('tests/test_analyze_default_dockerfile_parse.py'):
        ['python tests/test_analyze_default_dockerfile_parse.py'],
    re.compile('tests/test_class_command.py'):
        ['python tests/test_class_command.py'],
    re.compile('tests/test_class_oci_image.py'):
        ['python tests/test_class_oci_image.py'],
    re.compile('tests/test_class_docker_image.py'):
        ['python tests/test_class_docker_image.py',
         'tern report -w photon.tar'],
    re.compile('tests/test_class_file_data.py'):
        ['python tests/test_class_file_data.py'],
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
        ['python tests/test_class_template.py']}

alltests = []
for change in changes:
    for check, _ in test_suite.items():
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
