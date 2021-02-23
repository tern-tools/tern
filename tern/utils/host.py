import os

from tern.analyze.default.command_lib import command_lib


def check_shell():
    """Check if any shell binary is available on the host"""
    for shell in command_lib.command_lib["common"]["shells"]:
        if os.path.exists(shell):
            return shell
    return ""
