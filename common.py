'''
Common functions
'''
import sys

from utils import dockerfile as df
from utils import commands as cmds
from utils import cache as c

# constants strings
no_image_tag = '''No base image and/or tag listed in the command library \n
To add one, make an entry in command_lib/base.yml'''
no_command = '''No listing of hardcoded or retrieval steps for {image_tag} \n
To tell the tool this information make an entry in command_lib/base.yml'''
no_invocation = '''No invocation steps to perform within a container nor
on the host machine.\n To tell the tool how to retrieve this information,
make an entry in command_lib/base.yml'''


def check_cache_base(base_image_tag):
    '''Given a base image tag return a list of packages for the layers
    in the cache
    TODO: images and layers are used intergably for the base image
    Ideally the packages should be identified by the filesystem and the image
    ID'''
    image_tag_string = base_image_tag[0] + df.tag_separator + base_image_tag[1]
    if not cmds.check_image(image_tag_string):
        cmds.docker_command(cmds.pull, True, image_tag_string)
    image_id = cmds.get_image_id(image_tag_string)
    return c.get_packages(image_id)


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


def get_base_packages(base_image_tag):
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
