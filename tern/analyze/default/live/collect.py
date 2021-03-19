# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Functions to collect package metadata from a live container filesystem.

These functions are similar to the default collect.py functions except
the invoking of the scripts occurs in a different environment.
"""
import logging
import os
import re

from tern.utils import rootfs
from tern.utils import constants
from tern.analyze.default import collect as dcol

# global logger
logger = logging.getLogger(constants.logger_name)


def create_script(command, prereqs, method):
    """Create the script to execute in an unshared environment"""
    chroot_script = """#!{host_shell}

mount -t proc /proc {mnt}/proc
chroot {mnt} {fs_shell} -c "{snip}"
"""
    host_script = """#!{host_shell}
{host_shell} -c "{snip}"
"""
    script = ''
    script_path = os.path.join(rootfs.get_working_dir(), constants.script_file)
    if method == 'container':
        script = chroot_script.format(host_shell=prereqs.host_shell,
                                      mnt=prereqs.host_path,
                                      fs_shell=prereqs.fs_shell,
                                      snip=command)
    if method == 'host':
        script = host_script.format(host_shell=prereqs.host_shell,
                                    snip=command)
    with open(script_path, 'w') as f:
        f.write(script)
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


def invoke_live(snippet_list, prereqs, method):
    """Given a list of commands to run, invoke the commands and return
    the result. The prereqs object should"""
    # we first create a single command from the snippet list
    command = snippets_to_script(snippet_list)
    logger.debug("Invoking command: %s", command)
    # we then insert this command into our unshare script
    script_path = create_script(command, prereqs, method)
    if method == 'container':
        full_cmd = ['unshare', '-mpf', '-r', script_path]
    if method == 'host':
        full_cmd = ['unshare', '-pf', '-r', script_path]
    # invoke the script and remove it
    output, error = rootfs.shell_command(False, full_cmd)
    os.remove(script_path)
    return output, error


def get_attr_list(attr_dict, prereqs):
    """Similar to get_pkg_attrs in tern/analyze/default/collect.py but with
    invocation on a live container image"""
    error_msgs = ""
    result = ""
    if 'invoke' in attr_dict.keys():
        for step in range(1, len(attr_dict['invoke'].keys()) + 1):
            method, snippet_list = dcol.get_snippet_list(
                attr_dict['invoke'][step], prereqs)
            # invoke inventory script against the mount directory
            result, error = invoke_live(snippet_list, prereqs, method)
            if error:
                logger.warning(
                    "Error invoking command: %s", error.decode('utf-8'))
                error_msgs = error_msgs + error.decode('utf-8')
    if 'delimiter' in attr_dict.keys():
        res_list = result.decode('utf-8').split(attr_dict['delimiter'])
        if res_list[-1] == '' or res_list[-1] == '\n':
            res_list.pop()
            return res_list, error_msgs
        return res_list, error_msgs
    return result, error_msgs
