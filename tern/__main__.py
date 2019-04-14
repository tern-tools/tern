#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Tern executable
"""


import argparse
import logging
import os

from tern.report import report
from tern.utils import cache
from tern.utils import constants

# global logger
logger = logging.getLogger(constants.logger_name)
logger.setLevel(logging.DEBUG)

# console stream handler
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s - %(message)s')

log_handler = logging.FileHandler(constants.logfile, mode='w')
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(formatter)

console.setFormatter(formatter)

logger.addHandler(log_handler)


def do_main(args):
    '''Execute according to subcommands'''
    if args.log_stream:
        # set up console logs
        global logger
        global console
        logger.addHandler(console)
    logger.debug('Starting...')
    if args.clear_cache:
        logger.debug('Clearing cache...')
        cache.clear()
    if hasattr(args, 'name') and args.name == 'report':
        if args.dockerfile:
            report.execute_dockerfile(args)
        if args.docker_image:
            report.execute_docker_image(args)
        logger.debug('Report completed.')
    logger.debug('Finished')


def main():

    def check_file_existence(path):
        if not os.path.isfile(path):
            msg = "{}: does not exist".format(path)
            raise argparse.ArgumentTypeError(msg)
        return path

    parser = argparse.ArgumentParser(
        prog='Tern',
        description='''
           Tern is a container image component curation tool. Tern retrieves
    information about packages that are installed in a container image.
    Learn more at https://github.com/vmware/tern''')
    parser.add_argument('-l', '--log-stream', action='store_true',
                        help="Stream logs to the console;"
                        "Useful when running in a shell")
    parser.add_argument('-c', '--clear-cache', action='store_true',
                        help="Clear the cache before running")
    parser.add_argument('-k', '--keep-working-dir', action='store_true',
                        help="Keep the working directory after execution;"
                        "Useful when debugging container images")
    parser.add_argument('-b', '--bind-mount', action='store_true',
                        help="Treat working directory as a bind mount;"
                        "Needed when running from within a container")
    parser.add_argument('-r', '--redo', action='store_true',
                        help="Repopulate the cache for found layers")
    subparsers = parser.add_subparsers(help='Subcommands')
    # subparser for report
    parser_report = subparsers.add_parser('report',
                                          help="Create a report")
    parser_report.add_argument('-d', '--dockerfile', type=check_file_existence,
                               help="Dockerfile used to build the Docker"
                               " image")
    parser_report.add_argument('-i', '--docker-image',
                               help="Docker image that exists locally -"
                               " image:tag")
    parser_report.add_argument('-s', '--summary', action='store_true',
                               help="Summarize the report as a list of"
                               " packages with associated information")
    parser_report.add_argument('-y', '--yaml', action='store_true',
                               help="Create a report in yaml format")
    parser_report.add_argument('-j', '--json', action='store_true',
                               help="Create a report in json format")
    parser_report.add_argument('-f', '--file', default=None,
                               help="Write the report to a file; "
                               "If no file is given the default file in "
                               "utils/constants.py will be used")
    parser_report.set_defaults(name='report')
    args = parser.parse_args()

    # execute
    do_main(args)


if __name__ == "__main__":
    main()
