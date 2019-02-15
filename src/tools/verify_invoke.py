'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import argparse
import subprocess

from utils import constants
from command_lib import command_lib

'''
Test script for running commands using docker exec
This is used to test if your list of docker exec commands
produce expected results
'''


def look_up_lib(keys):
    '''Return the dictionary for the keys given
    Assuming that the keys go in order'''
    subd = command_lib.command_lib[keys.pop(0)]
    while keys:
        subd = subd[keys.pop(0)]
    return subd


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='''
        A script to test if the set of commands that get executed within
        a container produce expected results.
        Give a list of keys to point to in the command library and the
        image''')
    parser.add_argument('--container', default=constants.container,
                        help='Name of the running container')
    parser.add_argument('--keys', nargs='+',
                        help='List of keys to look up in the command library')
    parser.add_argument('--shell', default='/bin/bash',
                        help='The shell executable that the container uses')
    parser.add_argument('--package', default='',
                        help='A package name that the command needs to \
                        execute with')
    args = parser.parse_args()
    if 'snippets' in args.keys and 'packages' in args.keys:
        # we're looking up the snippet library
        # get the package info that corresponds to the package name
        # or get the default
        last = args.keys.pop()
        info_list = look_up_lib(args.keys)
        info_dict = command_lib.check_for_unique_package(info_list, args.package)[last]
    else:
        info_dict = look_up_lib(args.keys)
    try:
        result = command_lib.get_pkg_attr_list(
            args.shell, info_dict, args.package, False, args.container)
        print('Output list: ' + ' '.join(result[0]))
        print('Error messages: ' + result[1])
        print('Number of elements: ' + str(len(result[0])))
    except subprocess.CalledProcessError as error:
        print(error.output)
