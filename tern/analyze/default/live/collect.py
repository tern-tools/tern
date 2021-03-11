# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to collect package metadata from a live container filesystem.

These functions are similar to the default collect.py functions except
the invoking of the scripts occurs in a different environment.
"""
import os
import re

from tern.utils import rootfs
from tern.utils import constants
from tern.analyze.default import collect as dcol


def create_script(command, shell, mount):
    """Create the script to execute in an unshared environment"""
    script = """#!/bin/sh

mount -t proc /proc {mnt}/proc
chroot {mnt} {shell} -c "{snip}"
"""
    script_path = os.path.join(rootfs.get_working_dir(), constants.script_file)
    with open(script_path, 'w') as f:
        f.write(script.format(mnt=mount, shell=shell, snip=command))
    os.chmod(script_path, 0o700)
    return script_path


def snippets_to_script(snippet_list):
    """Create a script out of the snippet list such that it can be invokable
    via chroot's -c command"""
    replace_dict = {r'\$': r'\\$',
                    r'\`': r'\\`'}
    final_list = []
    for snippet in snippet_list:
        # replace the escaped characters
        for key in replace_dict.keys():
            snippet = re.sub(key, replace_dict[key], snippet)
        final_list.append(snippet)
    return " && ".join(final_list)


def invoke_live(snippet_list, shell, mount):
    """Given a list of commands to run, the shell that is used to run the
    commands, and the mount point, invoke the commands and return the result"""
    # we first create a single command from the snippet list
    command = snippets_to_script(snippet_list)
    # we then insert this command into our unshare script
    script_path = create_script(command, shell, mount)
    full_cmd = ['unshare', '-mpf', '-r', script_path]
    # invoke the script and remove it
    output, error = rootfs.shell_command(False, full_cmd)
    # os.remove(script_path)
    return output, error


def get_attr_list(attr_dict, shell, mount, work_dir=None, envs=None):
    """Similar to get_pkg_attrs in tern/analyze/default/collect.py but with
    invocation on a live container image"""
    error_msgs = ""
    result = ""
    if 'invoke' in attr_dict.keys():
        for step in range(1, len(attr_dict['invoke'].keys()) + 1):
            method, snippet_list = dcol.get_snippet_list(
                attr_dict['invoke'][step], work_dir, envs)
            if method == 'container':
                # invoke inventory script against the mount directory
                result, error = invoke_live(snippet_list, shell, mount)
                if error:
                    error_msgs = error_msgs + error.decode('utf-8')
    if 'delimiter' in attr_dict.keys():
        res_list = result.decode('utf-8').split(attr_dict['delimiter'])
        if res_list[-1] == '':
            res_list.pop()
            return res_list, error_msgs
        return res_list, error_msgs
    return result.decode('utf-8'), error_msgs
