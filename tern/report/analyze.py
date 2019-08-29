import logging

from tern.report import errors
from tern.report import formats
from tern.utils import constants
from tern.utils import rootfs
from tern.classes.notice import Notice
from tern.helpers import common
import tern.helpers.docker as dhelper
from tern.command_lib import command_lib

# global logger
logger = logging.getLogger(constants.logger_name)


def analyze_docker_image(image_obj, redo=False, dockerfile=False):
    '''Given a DockerImage object, for each layer, retrieve the packages, first
    looking up in cache and if not there then looking up in the command
    library. For looking up in command library first mount the filesystem
    and then look up the command library for commands to run in chroot'''

    # set up empty master list of packages
    master_list = []
    prepare_for_analysis(image_obj, dockerfile)
    binary = common.get_base_bin()
    # Get the shell to be used
    shell = get_shell(image_obj, binary)
    # Analyse the first layer
    analyze_first_layer(binary, image_obj, shell, master_list, redo)
    # Analyse the remaining layers
    analyze_subsequent_layers(image_obj, shell, master_list, redo)
    common.save_to_cache(image_obj)


def get_shell(image_obj, binary):
    # set up a notice origin referring to the base command library listing
    origin_command_lib = formats.invoking_base_commands
    # find the shell to invoke commands in
    shell, _ = command_lib.get_image_shell(
        command_lib.get_base_listing(binary))
    if not shell:
        # add a warning notice for no shell in the command library
        logger.warning('No shell listing in command library. '
                       'Using default shell')
        no_shell_message = errors.no_shell_listing.format(
            binary=binary, default_shell=constants.shell)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_command_lib, Notice(no_shell_message, 'warning'))
        # add a hint notice to add the shell to the command library
        add_shell_message = errors.no_listing_for_base_key.format(
            listing_key='shell')
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_command_lib, Notice(add_shell_message, 'hint'))
        shell = constants.shell

    return shell


def prepare_for_analysis(image_obj, dockerfile):
    # find the layers that are imported
    if dockerfile:
        dhelper.set_imported_layers(image_obj)
    # add notices for each layer if it is imported
    image_setup(image_obj)


def analyze_first_layer(binary, image_obj, shell, master_list, redo):
    # find the binary by mounting the base layer
    target = rootfs.mount_base_layer(image_obj.layers[0].tar_file)

    # set up a notice origin for the first layer
    origin_first_layer = 'Layer: ' + image_obj.layers[0].fs_hash[:10]
    # only extract packages if there is a known binary and the layer is not
    # cached
    if binary:
        if not common.load_from_cache(image_obj.layers[0], redo):
            # Determine pacakge/os style from binary in the image layer
            common.get_os_style(image_obj.layers[0], binary)
            # get the packages of the first layer
            rootfs.prep_rootfs(target)
            common.add_base_packages(image_obj.layers[0], binary, shell)
            # unmount proc, sys and dev
            rootfs.undo_mount()
    else:
        logger.warning(errors.no_package_manager)
        # /etc/os-release may still be present even if binary is not
        common.get_os_style(image_obj.layers[0], None)
        image_obj.layers[0].origins.add_notice_to_origins(
            origin_first_layer, Notice(errors.no_package_manager, 'warning'))
        # no binary means there is no shell so set to default shell
        logger.warning('Unknown filesystem. Using default shell')
        shell = constants.shell
    # unmount the first layer
    rootfs.unmount_rootfs()
    # populate the master list with all packages found in the first layer
    for p in image_obj.layers[0].packages:
        master_list.append(p)


def analyze_subsequent_layers(image_obj, shell, master_list, redo):
    # get packages for subsequent layers
    curr_layer = 1
    while curr_layer < len(image_obj.layers):
        if not common.load_from_cache(image_obj.layers[curr_layer], redo):
            # get commands that created the layer
            # for docker images this is retrieved from the image history
            command_list = dhelper.get_commands_from_history(
                image_obj.layers[curr_layer])
            if command_list:
                # mount diff layers from 0 till the current layer
                target = mount_overlay_fs(image_obj, curr_layer)
                # mount dev, sys and proc after mounting diff layers
                rootfs.prep_rootfs(target)
            # for each command look up the snippet library
            for command in command_list:
                pkg_listing = command_lib.get_package_listing(command.name)
                if isinstance(pkg_listing, str):
                    common.add_base_packages(
                        image_obj.layers[curr_layer], pkg_listing, shell)
                else:
                    common.add_snippet_packages(
                        image_obj.layers[curr_layer], command, pkg_listing,
                        shell)
            if command_list:
                rootfs.undo_mount()
                rootfs.unmount_rootfs()
        # update the master list
        common.update_master_list(master_list, image_obj.layers[curr_layer])
        curr_layer = curr_layer + 1


def image_setup(image_obj):
    '''Add notices for each layer'''
    for layer in image_obj.layers:
        origin_str = 'Layer: ' + layer.fs_hash[:10]
        layer.origins.add_notice_origin(origin_str)
        if layer.import_str:
            layer.origins.add_notice_to_origins(origin_str, Notice(
                'Imported in Dockerfile using: ' + layer.import_str, 'info'))


def mount_overlay_fs(image_obj, top_layer):
    '''Given the image object and the top most layer, mount all the layers
    until the top layer using overlayfs'''
    tar_layers = []
    for index in range(0, top_layer + 1):
        tar_layers.append(image_obj.layers[index].tar_file)
    target = rootfs.mount_diff_layers(tar_layers)
    return target
