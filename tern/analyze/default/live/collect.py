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
        for key in replace_dict:
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
