import argparse
import subprocess

import utils.commands as cmds

'''
Test script for running commands using docker exec
This is used to test if your list of docker exec commands
produce expected results
'''


def look_up_lib(keys):
    '''Return the dictionary for the keys given
    Assuming that the keys go in order'''
    subd = cmds.command_lib[keys.pop(0)]
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
    parser.add_argument('--container', default=cmds.container,
                        help='Name of the running container')
    parser.add_argument('--keys', nargs='+',
                        help='List of keys to look up in the command library')
    parser.add_argument('--shell', default='/bin/bash',
                        help='The shell executable that the container uses')
    parser.add_argument('--package', default='',
                        help='A package name that the command needs to \
                        execute with')
    args = parser.parse_args()
    info_dict = look_up_lib(args.keys)
    invoke_dict = info_dict['invoke']
    delimiter = info_dict['delimiter']
    for step in range(1, len(invoke_dict.keys()) + 1):
        try:
            result = cmds.invoke_in_container(invoke_dict[step]['container'],
                                              args.shell,
                                              override=args.container)
            result = result[:-1]
            # print(result)
            res_list = result.split(delimiter)
            if res_list[-1] == '':
                res_list.pop()
            print(res_list)
            print(len(res_list))
        except subprocess.CalledProcessError as error:
            print(error.output)
