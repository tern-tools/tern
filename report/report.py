'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging

from utils.container import check_image
from utils.container import start_container
from utils.container import remove_container
from utils.container import remove_image
from utils import constants as const
from utils import cache
import common
import docker

'''
Create a report
'''

def write_report(report):
    '''Write the report to a file'''
    with open(const.report_file, 'w') as f:
        f.write(report)


def setup(dockerfile=None):
    '''Any initial setup'''
    # load the cache
    cache.load()
    # load dockerfile if present
    if dockerfile:
        docker.load_docker_commands(dockerfile)


def load_base_image():
    '''Create base image from dockerfile instructions and return the image'''
    base_image = docker.get_dockerfile_base()
    base_instructions_str = docker.print_dockerfile_base()
    # try to get image metadata
    if check_image(base_image.repotag):
        try:
            base_image.load_image()
        except NameError as error:
            name_error_notice = Notice(
                base_instructions_str, str(error), 'error')
            base_image.add_notice(name_error_notice)
        except subprocess.CalledProcessError as error:
            docker_exec_notice = Notice(
                base_instructions_str, str(error.output, 'utf-8'), 'error')
            base_image.add_notice(docker_exec_notice)
        except IOError as error:
            extract_error_notice = Notice(
                base_instructions_str, str(error), 'error')
            base_image.add_notice(extract_error_notice)
    return base_image


def execute_dockerfile(args):
    '''Execution path if given a dockerfile'''
    # logging
    logger = logging.getLogger(const.logger_name)
    setup(args.dockerfile)
    # ----------------------------------------------------
    # Step 1: Get the packages installed in the base image
    # ----------------------------------------------------
    base_image = load_base_image()
    if len(base_image.notices) == 0:
        # load any packages from cache
        if not common.load_from_cache(base_image):
            # load any packages using the command library
            start_container(base_image.repotag)
            common.add_base_packages(base_image)
    else:
        # don't attempt to build further; try to parse Dockerfile

    # ----------------------------------------------------
    # Step 2: Get the packages installed in the given image
    # ----------------------------------------------------
    # get a list of packages that may be installed from the dockerfile
    build, msg = common.is_build()
    if build:
        # get the shell that we will use for all the commands
        shell = common.get_image_shell(base_image_msg[0])
        # start a container with the built image
        image_tag_string = common.get_dockerfile_image_tag()
        start_container(image_tag_string)
        report = print_dockerfile_run(report, shell, len(base_obj_list),
                                      master_list, args.summary, logger)
        # remove container when done
        remove_container()
        remove_image(image_tag_string)
    else:
        # Dockerfile does not build, so get packages from dockerfile
        # parsing only
        pkg_dict = common.get_dockerfile_packages()
        report = report + env_dep_dockerfile.format(build_fail_msg=msg)
        report = report + checking_against_snippets
        report = report + 'Packages from parsing Dockerfile RUN commands:\n'
        for pkg in pkg_dict['recognized']:
            report = report + ' ' + pkg
        report = report + '\nUnregonized RUN commands in Dockerfile:\n'
        for cmd in pkg_dict['unrecognized']:
            report = report + cmd + '\n'
    common.save_cache()
    write_report(report)
