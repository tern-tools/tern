'''
Common functions
'''
from classes.layer import Layer
from classes.package import Package
from utils import dockerfile as df
from utils import commands as cmds
from utils import cache as cache
from utils import metadata as meta

# constants strings
no_image_tag = '''No base image and/or tag listed in the command library \n
To add one, make an entry in command_lib/base.yml'''
no_command = '''No listing of hardcoded or retrieval steps for {image_tag} \n
To tell the tool this information make an entry in command_lib/base.yml'''
no_invocation = '''No invocation steps to perform within a container nor
on the host machine.\n To tell the tool how to retrieve this information,
make an entry in command_lib/base.yml'''
base_image_not_found = '''Failed to pull the base image. Perhaps it was
removed from Dockerhub'''
cannot_extract_base_image = '''Failed to extact base image. This shouldn't
happen'''

# dockerfile commands
docker_commands = []


def load_docker_commands(dockerfile):
    '''Given a dockerfile get a persistent list of docker commands'''
    global docker_commands
    # TODO: some checks on the passed argument would be nice here
    docker_commands = df.get_directive_list(df.get_command_list(dockerfile))


def check_base(base_image_tag):
    '''Given a base image tag check if an image exists
    If not then try to pull the image.'''
    image_tag_string = base_image_tag[0] + df.tag_separator + base_image_tag[1]
    success = cmds.check_image(image_tag_string)
    if not success:
        result = cmds.docker_command(cmds.pull, True, image_tag_string)
        if result is None:
            print(base_image_not_found)
            success = False
    return success


def get_base_layers(base_image_tag):
    '''Given the base image and tag, get the base layers
    Note: this assumes that the image exists locally'''
    base_layers = []
    image_tag_string = base_image_tag[0] + df.tag_separator + base_image_tag[1]
    if not cmds.extract_image_metadata(image_tag_string):
        # there was some error in extracting the metadata so we cannot
        # find the context for the base image
        print(cannot_extract_base_image)
        raise
    else:
        # we should now have a place to extract metadata
        base_layers = meta.get_image_layers(meta.get_image_manifest())
    return base_layers


def get_base_dict(base_image_tag):
    '''Return the base dictionary from the command library'''
    image = base_image_tag[0]
    # check image
    listing = cmds.query_library(['base', image])
    if listing:
        if base_image_tag[1] == 'latest':
            tag = cmds.query_library(['base', image, 'latest'])
        else:
            tag = base_image_tag[1]
        # check tag
        listing = cmds.query_library(['base', image, tag])
    return listing


def invoke_base_packages(base_image_tag):
    '''Get the list of packages that are installed in the base layer using
    the invocations listed in the base command library
    If they don't exist inform the user'''
    # TODO: all of the commands listed so far are invoked within a container
    # there should be some mechanism where the commands get executed one
    # by one but also outside and inside the container
    image_tag_string = base_image_tag[0] + df.tag_separator + base_image_tag[1]
    base_dict = get_base_dict(base_image_tag)
    package_list = []
    if base_dict:
        names_dict = base_dict.get('names')
        if names_dict:
            package_list = cmds.invoke_in_container(
                names_dict['container']['invoke'], image_tag_string,
                base_dict['shell'])
        else:
            print(no_command.format(image_tag=image_tag_string))
    else:
        print(no_image_tag)
    return package_list


def get_base_obj():
    '''Given a Dockerfile get a list of layers with their associated packages:
        1. Get the base image and tag
        2. Check if the base image exists on the host machine
        3. Get the layers
        4. For each layer check if there is a list of packages associated
        with it in the cache
        5. If there are no packages return a list of empty layer objects'''
    obj_list = []
    # get the base image and tag
    base_image_tag = df.get_base_image_tag(
        df.get_base_instructions(docker_commands))
    if not check_base:
        # the base image cannot be found locally nor remotely
        # at this point there is no context for Tern to use so raise an
        # exception to exit gracefully
        print(base_image_not_found)
        raise
    else:
        # get the layers
        layer_files = get_base_layers(base_image_tag)
        for layer_file in layer_files:
            layer = Layer(meta.get_layer_sha(layer_file))
            package_list = cache.get_packages(meta.get_layer_sha(layer_file))
            for package in package_list:
                pkg_obj = Package(package['name'])
                pkg_obj.fill(package)
                layer.add(pkg_obj)
            obj_list.append(layer)
    return obj_list
