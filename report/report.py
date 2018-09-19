'''
Copyright (c) 2017-2018 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import logging
import os
import shutil
import subprocess
import sys

from report import content
from report import errors
from report import formats
from utils import container
from utils import constants
from utils import cache
from utils import general
from utils import rootfs
from classes.docker_image import DockerImage
from classes.image import Image
from classes.image_layer import ImageLayer
from classes.notice import Notice
from classes.package import Package
import common
import docker
from command_lib import command_lib

'''
Create a report
'''

# global logger
logger = logging.getLogger(constants.logger_name)


def write_report(report):
    '''Write the report to a file'''
    with open(constants.report_file, 'w') as f:
        f.write(report)


def setup(dockerfile=None, image_tag_string=None):
    '''Any initial setup'''
    # generate random names for image, container, and tag
    general.initialize_names()
    # load the cache
    cache.load()
    # load dockerfile if present
    if dockerfile:
        docker.load_docker_commands(dockerfile)
    # check if the docker image is present
    if image_tag_string:
        if not container.check_image(image_tag_string):
            logger.fatal(errors.cannot_find_image.format(
                imagetag=image_tag_string))
            sys.exit()
    # create temporary working directory
    if not os.path.exists(constants.temp_folder):
        os.mkdir(constants.temp_folder)
    # set up folders for rootfs operations
    rootfs.set_up()


def teardown():
    '''Tear down tern setup'''
    # save the cache
    cache.save()
    # remove folders for rootfs operations
    rootfs.clean_up()


def clean_image_tars(image_obj):
    '''Clean up untar directories'''
    for layer in image_obj.layers:
        fspath = rootfs.get_untar_dir(layer.tar_file)
        if os.path.exists(fspath):
            rootfs.root_command(rootfs.remove, fspath)


def load_base_image():
    '''Create base image from dockerfile instructions and return the image'''
    base_image, dockerfile_lines = docker.get_dockerfile_base()
    # try to get image metadata
    if not container.check_image(base_image.repotag):
        container.pull_image(base_image.repotag)
    try:
        base_image.load_image()
    except NameError as error:
        logger.warning('Error in loading base image: ' + str(error))
        base_image.origins.add_notice_to_origins(
            dockerfile_lines, Notice(str(error), 'error'))
    except subprocess.CalledProcessError as error:
        logger.warning(
            'Error in loading base image: ' + str(error.output, 'utf-8'))
        base_image.origins.add_notice_to_origins(
            dockerfile_lines, Notice(str(error.output, 'utf-8'), 'error'))
    except IOError as error:
        logger.warning('Error in loading base image: ' + str(error))
        base_image.origins.add_notice_to_origin(
            dockerfile_lines, Notice(str(error), 'error'))
    return base_image


def load_full_image(image_tag_string):
    '''Create image object from image name and tag and return the object'''
    test_image = DockerImage(image_tag_string)
    failure_origin = formats.image_load_failure.format(
        testimage=test_image.repotag)
    try:
        test_image.load_image()
    except NameError as error:
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error), 'error'))
    except subprocess.CalledProcessError as error:
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error.output, 'utf-8'), 'error'))
    except IOError as error:
        test_image.origins.add_notice_to_origins(
            failure_origin, Notice(str(error), 'error'))
    return test_image


def image_setup(image_obj):
    '''Add notices for each layer'''
    for layer in image_obj.layers:
        origin_str = 'Layer: ' + layer.fs_hash[:10]
        layer.origins.add_notice_origin(origin_str)
        if layer.import_str:
            layer.origins.add_notice_to_origins(origin_str, Notice(
                'Imported in Dockerfile using: ' + layer.import_str, 'info'))


def analyze_docker_image(image_obj, dockerfile=False):
    '''Given a DockerImage object, for each layer, retrieve the packages, first
    looking up in cache and if not there then looking up in the command
    library. For looking up in command library first mount the filesystem
    and then look up the command library for commands to run in chroot'''
    # find the layers that are imported
    if dockerfile:
        docker.set_imported_layers(image_obj)
    # add notices for each layer if it is imported
    image_setup(image_obj)
    shell = ''
    # set up empty master list of package names
    master_list = []
    # find the binary by mounting the base layer
    target = rootfs.mount_base_layer(image_obj.layers[0].tar_file)
    binary = common.get_base_bin(image_obj.layers[0])
    # set up a notice origin referring to the base command library listing
    origin_command_lib = formats.invoking_base_commands
    # find the shell to invoke commands in
    shell, msg = command_lib.get_image_shell(
        command_lib.get_base_listing(binary))
    if not shell:
        # add a warning notice for no shell in the command library
        logger.warning('No shell listing in command library. '
                       'Using default shell')
        no_shell_message = errors.no_shell_listing.format(
            binary, default_shell=constants.shell)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_command_lib, Notice(no_shell_message, 'warning'))
        # add a hint notice to add the shell to the command library
        add_shell_message = errors.no_listing_for_base_key.format(
            listing_key='shell')
        image_obj.layers[0].origins.add_notice_origins(
            origin_command_lib, Notice(add_shell_message, 'hint'))
        shell = constants.shell
    # only extract packages if there is a known binary and the layer is not
    # cached
    if binary:
        if not common.load_from_cache(image_obj.layers[0]):
            # get the packages of the first layer
            rootfs.prep_rootfs(target)
            common.add_base_packages(image_obj.layers[0], binary, shell)
            # unmount proc, sys and dev
            rootfs.undo_mount()
    else:
        logger.warning(errors.unrecognized_base.format(
            image_name=image_obj.name, image_tag=image_obj.tag))
    # unmount the first layer
    rootfs.unmount_rootfs()
    # populate the master list with all packages found in the first layer
    # can't use assignment as that will just point to the image object's layer
    for p in image_obj.layers[0].get_package_names():
        master_list.append(p)
    # get packages for subsequent layers
    curr_layer = 1
    while curr_layer < len(image_obj.layers):
        if not common.load_from_cache(image_obj.layers[curr_layer]):
            # get commands that created the layer
            # for docker images this is retrieved from the image history
            command_list = docker.get_commands_from_history(
                image_obj.layers[curr_layer])
            # mount diff layers from 0 till the current layer
            tar_layers = []
            for index in range(0, curr_layer + 1):
                tar_layers.append(image_obj.layers[index].tar_file)
            target = rootfs.mount_diff_layers(tar_layers)
            # mount dev, sys and proc after mounting diff layers
            rootfs.prep_rootfs(target)
            # for each command look up the snippet library
            for command in command_list:
                pkg_listing = command_lib.get_package_listing(command.name)
                if type(pkg_listing) is str:
                    common.add_base_packages(
                        image_obj.layers[curr_layer], pkg_listing, shell)
                else:
                    common.add_snippet_packages(
                        image_obj.layers[curr_layer], command, shell)
            rootfs.undo_mount()
            rootfs.unmount_rootfs()
        # update the master list
        common.update_master_list(master_list, image_obj.layers[curr_layer])
        curr_layer = curr_layer + 1
    common.save_to_cache(image_obj)


def get_dockerfile_packages():
    '''Given a Dockerfile return an approximate image object. This is mosty
    guess work and shouldn't be relied on for accurate information. Add
    Notice messages indicating as such:
        1. Create an image with a placeholder repotag
        2. For each RUN command, create a package list
        3. Create layer objects with incremental integers and add the package
        list to that layer with a Notice about parsing
        4. Return stub image'''
    stub_image = Image('easteregg:cookie')
    layer_count = 0
    for inst in docker.docker_commands:
        if inst[0] == 'RUN':
            layer_count = layer_count + 1
            layer = ImageLayer(layer_count)
            install_commands, msg = common.filter_install_commands(inst[1])
            if msg:
                layer.origins.add_notice_to_origins(
                    inst[1], Notice(msg, 'info'))
            pkg_names = []
            for command in install_commands:
                pkg_names.append(common.get_installed_package_names(command))
            for pkg_name in pkg_names:
                pkg = Package(pkg_name)
                # shell parser does not parse version pins yet
                # when that is enabled, Notices for no versions need to be
                # added here
                layer.add_package(pkg)
    return stub_image


def generate_report(args, *images):
    '''Generate a report based on the command line options'''
    logger.debug('Writing report...')
    report = formats.disclaimer
    if args.summary:
        for image in images:
            report = report + content.print_summary_report(image)
    else:
        for image in images:
            report = report + content.print_full_report(image)
    write_report(report)


def check_docker_daemon():
    '''Check if the Docker daemon is running. If not, exit gracefully'''
    try:
        container.docker_command(['docker', 'ps'])
    except subprocess.CalledProcessError as error:
        logger.error('Docker daemon is not running: {0}'.format(
            error.output.decode('utf-8')))
        sys.exit()


def execute_dockerfile(args):
    '''Execution path if given a dockerfile'''
    check_docker_daemon()
    logger.debug('Setting up...')
    setup(dockerfile=args.dockerfile)
    # attempt to build the image
    logger.debug('Building Docker image...')
    # placeholder to check if we can analyze the full image
    completed = True
    build, msg = docker.is_build()
    if build:
        # attempt to get built image metadata
        image_tag_string = docker.get_dockerfile_image_tag()
        full_image = load_full_image(image_tag_string)
        if full_image.origins.is_empty():
            # image loading was successful
            # Add an image origin here
            full_image.origins.add_notice_origin(
                formats.dockerfile_image.format(dockerfile=args.dockerfile))
            # analyze image
            analyze_docker_image(full_image, True)
        else:
            # we cannot load the full image
            logger.warning('Cannot retrieve full image metadata')
            completed = False
        # clean up image
        container.remove_image(full_image.repotag)
        if not args.keep_working_dir:
            clean_image_tars(full_image)
    else:
        # cannot build the image
        logger.warning('Cannot build image')
        completed = False
    # check if we have analyzed the full image or not
    if not completed:
        # get the base image
        logger.debug('Loading base image...')
        base_image = load_base_image()
        if base_image.origins.is_empty():
            # image loading was successful
            # add a notice stating failure to build image
            base_image.origins.add_notice_to_origins(
                args.dockerfile, Notice(
                    formats.image_build_failure, 'warning'))
            # analyze image
            analyze_docker_image(base_image)
        else:
            # we cannot load the base image
            logger.warning('Cannot retrieve base image metadata')
        # run through commands in the Dockerfile
        logger.debug('Parsing Dockerfile to generate report...')
        stub_image = get_dockerfile_packages()
        # clean up image
        container.remove_image(base_image.repotag)
        if not args.keep_working_dir:
            clean_image_tars(base_image)
    # generate report based on what images were created
    if completed:
        generate_report(args, full_image)
    else:
        generate_report(args, base_image, stub_image)
    logger.debug('Teardown...')
    teardown()
    if not args.keep_working_dir:
        shutil.rmtree(os.path.abspath(constants.temp_folder))


def execute_docker_image(args):
    '''Execution path if given a Docker image'''
    check_docker_daemon()
    logger.debug('Setting up...')
    setup(image_tag_string=args.docker_image)
    # attempt to get built image metadata
    full_image = load_full_image(args.docker_image)
    if full_image.origins.is_empty():
        # image loading was successful
        # Add an image origin here
        full_image.origins.add_notice_origin(
            formats.docker_image.format(imagetag=args.docker_image))
        # analyze image
        analyze_docker_image(full_image)
        # generate report
        generate_report(args, full_image)
    else:
        # we cannot load the full image
        logger.warning('Cannot retrieve full image metadata')
    if not args.keep_working_dir:
        clean_image_tars(full_image)
    logger.debug('Teardown...')
    teardown()
    if not args.keep_working_dir:
        shutil.rmtree(os.path.abspath(constants.temp_folder))
