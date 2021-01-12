#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
Tern executable
"""


import argparse
import logging
import os
import sys

from tern.utils import cache
from tern.utils import constants
from tern.utils import general
from tern import prep
from tern.analyze.default.container import run as crun
from tern.analyze.default.dockerfile import run as drun
from tern.analyze.default.debug import run as derun
from tern.report import errors


# global logger
from tern.utils.general import check_image_string

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


def check_file_existence(path):
    if not os.path.isfile(path):
        msg = "{}: does not exist".format(path)
        raise argparse.ArgumentTypeError(msg)
    return path


def get_version():
    '''Return the version string for the --version command line option'''
    ver_type, commit_or_ver = general.get_git_rev_or_version()
    message = ''
    if ver_type == "package":
        message = "Tern version {}".format(commit_or_ver)
    else:
        message = "Tern at commit {}".format(commit_or_ver)
    return message


def do_main(args):
    """Execute according to subcommands"""
    # Set up environment
    if not args.quiet:
        # set up console logs
        global logger
        global console
        logger.addHandler(console)
        logger.debug("Starting...")
    prep.setup(args.working_dir)
    if args.clear_cache:
        logger.debug('Clearing cache...')
        cache.clear()
    if hasattr(args, 'name'):
        if args.name == 'lock':
            drun.execute_dockerfile(args, True)
        elif args.name == 'report':
            if args.dockerfile:
                drun.execute_dockerfile(args)
            elif args.docker_image:
                # Check if the image string is a tarball
                if general.check_tar(args.docker_image):
                    logger.critical(errors.incorrect_raw_option)
                    sys.exit(1)
                # Check if the image string has the right format
                if not check_image_string(args.docker_image):
                    logger.critical(errors.incorrect_image_string_format)
                    sys.exit(1)
                # If the checks are OK, execute for docker image
                crun.execute_image(args)
        elif args.name == 'debug':
            derun.execute_debug(args)
    # Tear down the environment
    prep.teardown(args.keep_wd)
    logger.debug('Finished')


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='Tern',
        description='''
    Tern is a container image component curation tool. Tern retrieves
    information about packages that are installed in a container image.
    Learn more at https://github.com/tern-tools/tern''')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="Silences the output to the terminal;"
                        "Useful when logging behaviour unnecessary")
    parser.add_argument('-c', '--clear-cache', action='store_true',
                        help="Clear the cache before running")
    parser.add_argument('-k', '--keep-wd', action='store_true',
                        help="Keep the working directory after execution."
                        " Useful when debugging container images")
    parser.add_argument('-r', '--redo', action='store_true',
                        help="Repopulate the cache for found layers")
    parser.add_argument('-wd', '--working-dir', metavar='PATH',
                        help="Change default working directory to specified"
                        " absolute path.")
    parser.add_argument('-dr', '--driver', metavar="DRIVER_OPTION",
                        help="Required when running Tern in a container."
                        "Using 'fuse' will enable the fuse-overlayfs driver "
                        "to mount the diff layers of the container. If no "
                        "input is provided, 'fuse' will be used as the "
                        "default option.")

    # sys.version gives more information than we care to print
    py_ver = sys.version.replace('\n', '').split('[')[0]
    parser.add_argument('-v', '--version', action='version',
                        version="{ver_str}\n   python version = {py_v}".format(
                            ver_str=get_version(), py_v=py_ver))
    subparsers = parser.add_subparsers(help='Subcommands')

    # subparser for report
    parser_report = subparsers.add_parser('report',
                                          help="Create a BoM report."
                                          " Run 'tern report -h' for"
                                          " report format options.")
    parser_report.add_argument('-d', '--dockerfile', type=check_file_existence,
                               help="Dockerfile used to build the Docker"
                               " image")
    parser_report.add_argument('-i', '--docker-image',
                               help="Docker image that exists locally -"
                               " image:tag"
                               " The option can be used to pull docker"
                               " images by digest as well -"
                               " <repo>@<digest-type>:<digest>")
    parser_report.add_argument('-w', '--raw-image', metavar='FILE',
                               help="Raw container image that exists locally "
                               "in the form of a tar archive.")
    parser_report.add_argument('-x', '--extend', metavar='EXTENSION',
                               help="Use an extension to analyze a container "
                               "image. Available extensions:\n cve-bin-tool\n"
                               "scancode\n")
    parser_report.add_argument('-f', '--report-format',
                               metavar='REPORT_FORMAT',
                               help="Format the report using one of the "
                               "available formats: "
                               "spdxtagvalue, spdxjson, json, yaml, html")
    parser_report.add_argument('-o', '--output-file', default=None,
                               metavar='FILE',
                               help="Write the report to a file. "
                               "If no file is given the report will be "
                               "printed to the console.")
    parser_report.set_defaults(name='report')

    # subparser for dockerfile lock
    parser_lock = subparsers.add_parser('lock',
                                        help="Create an annotated Dockerfile"
                                        " that will pin the information "
                                        "it finds. Use this option to help "
                                        "achieve a more repeatable "
                                        "container image build.")
    parser_lock.add_argument('lock', metavar='DOCKERFILE',
                             help="Dockerfile that you want to lock.")
    parser_lock.add_argument('-o', '--output-file', default=None,
                             metavar='FILE', help="Write the "
                             "annotated Dockerfile to a file. If no report "
                             "is given, a new file, Dockerfile.new, will "
                             "be created in the current directory.")
    parser_lock.add_argument('-x', '--extend', metavar='EXTENSION',
                             help="Use an extension to analyze a container "
                             "image. Available extensions:\n cve-bin-tool\n"
                             "scancode\n")
    parser_lock.set_defaults(name='lock')

    # subparser for container "debug"
    parser_debug = subparsers.add_parser('debug',
                                         help="Debug pieces of operation by "
                                         "themselves. This is useful when "
                                         "debugging scripts entered into the "
                                         "command library or drivers used "
                                         "for mounting the container image "
                                         "layers.")
    parser_debug.add_argument('--recover', action='store_true',
                              help="If an unexpected error occurs during "
                              "mounting of the filesystem and device nodes, "
                              "recover the filesystem by undoing all the "
                              "mounts.")
    parser_debug.add_argument('-i', '--docker-image',
                              help="Docker image that exists locally -"
                              " image:tag"
                              " The option can be used to pull docker"
                              " images by digest as well -"
                              " <repo>@<digest-type>:<digest>")
    parser_debug.add_argument('-w', '--raw-image', metavar='FILE',
                              help="Raw container image that exists locally "
                              "in the form of a tar archive.")
    parser_debug.add_argument('--keys', nargs='+',
                              help="List of keys to look up in the command "
                              "library. Eg: base dpkg names")
    parser_debug.add_argument('--shell', default='/bin/sh',
                              help="The shell executable that the image uses")
    parser_debug.add_argument('--package', default='',
                              help="A package name that the command needs to "
                              "execute with. Useful when testing commands in "
                              "the snippet library")
    parser_debug.add_argument('--step', action='store_true',
                              help="An interactive mode in which the "
                              "container image will be mounted upto the given "
                              "layer and provide an environment to explore "
                              "the filesystem at that layer ")
    parser_debug.set_defaults(name='debug')

    args = parser.parse_args()

    # execute
    if sys.version_info < (3, 0):
        sys.stderr.write("Error running Tern. Please check that python3 "
                         "is configured as default.\n")
    else:
        do_main(args)


if __name__ == "__main__":
    main()
