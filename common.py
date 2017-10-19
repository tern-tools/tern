'''
Common functions
'''
import subprocess

from classes.layer import Layer
from classes.package import Package
from utils import dockerfile as df
from utils import commands as cmds
from utils import cache as cache
from utils import metadata as meta

# constants strings
dockerfile_using_latest = '''The Dockerfile provided does not have a base
image or it is using 'latest'. Falling back on the default in the command
library. Consider adding a tag to the FROM line
(for example: FROM debian:jessie)'''
no_image_tag_listing = \
    '''No listing of {image}:{tag} in the command library. To add one, make an
entry in command_lib/base.yml'''
no_command = '''No listing of hardcoded or retrieval steps for {image_tag} \n
To tell the tool this information make an entry in command_lib/base.yml'''
no_invocation = '''No invocation steps to perform within a container nor
on the host machine.\n To tell the tool how to retrieve this information,
make an entry in command_lib/base.yml'''
base_image_not_found = '''Failed to pull the base image. Perhaps it was
removed from Dockerhub'''
cannot_extract_base_image = '''Failed to extact base image. This shouldn't
happen'''
incomplete_command_lib_listing = '''The command library has an incomplete
listing for {image}:{tag}. Please complete the listing based on the examples'''
cannot_retrieve_base_packages = '''Cannot retrieve the packages in the base
image {image}:{tag}. Check the command listing in the command library'''
docker_build_failed = '''Unable to build docker image using Dockerfile
{dockerfile}: {error_msg}'''

# dockerfile
dockerfile = ''
# dockerfile commands
docker_commands = []


def load_docker_commands(dockerfile_path):
    '''Given a dockerfile get a persistent list of docker commands'''
    global docker_commands
    # TODO: some checks on the passed argument would be nice here
    docker_commands = df.get_directive_list(df.get_command_list(
        dockerfile_path))
    global dockerfile
    dockerfile = dockerfile_path


def get_dockerfile_base():
    '''Check if the dockerfile's FROM has the 'latest' tag and if so
    report a message'''
    base_image_tag = df.get_base_image_tag(df.get_base_instructions(
        docker_commands))
    if base_image_tag[1] == 'latest':
        new_image_tag = (base_image_tag[0],
                         cmds.get_latest_tag(base_image_tag[0]))
        return (new_image_tag, dockerfile_using_latest)
    else:
        return (base_image_tag, '')


def print_dockerfile_base():
    '''For the purpose of tracking the lines in the dockerfile that
    produce packages, return a string containing the lines in the dockerfile
    that pertain to the base image'''
    base_instr = ''
    for instr in df.get_base_instructions(docker_commands):
        base_instr = base_instr + instr[0] + ' ' + instr[1] + '\n'
    return base_instr


def get_image_shell(base_image_tag):
    '''Given the base image tag tuple
    (<image>, <tag>) look up the base library for the shell'''
    return cmds.command_lib[
        'base'][base_image_tag[0]]['tags'][base_image_tag[1]]['shell']


def check_base_image(base_image_tag):
    '''Given a base image tag check if an image exists
    If not then try to pull the image.'''
    image_tag_string = base_image_tag[0] + df.tag_separator + base_image_tag[1]
    success = cmds.check_image(image_tag_string)
    if not success:
        result = cmds.docker_command(cmds.pull, image_tag_string)
        if result is None:
            print(base_image_not_found)
            success = False
    return success


def get_image_tag_string(image_tag_tuple):
    '''Given a tuple of the image and tag, return a string containing
    the image and tag'''
    return image_tag_tuple[0] + df.tag_separator + image_tag_tuple[1]


def process_base_invoke(invoke_dict, image_tag_string, shell):
    '''The invoke dictionary looks like this:
        <step number>: <environment>: <list of commands>
    1. Find out if there are any container environments if there are
    then start a container
    2. For each step invoke the commands
    NOTE: So far there are no host commands so we will just invoke the
    container ones'''
    for step in invoke_dict.keys():
        if 'container' in invoke_dict[step].keys():
            cmds.start_container(image_tag_string)
            break
    for step in range(1, len(invoke_dict.keys()) + 1):
        if 'container' in invoke_dict[step].keys():
            result = cmds.invoke_in_container(
                invoke_dict[step]['container'], shell)
    return result


def get_info_list(info_dict, info, image_tag_string):
    '''The info dictionary lives under the image and tag name in the base
    command library. It looks like this:
        <names>: list of names or snippets to invoke
        <versions>: list of versions or snippets to invoke
        <licenses>: list of license information or snippets to invoke
        <src_urls>: list of source urls or snippets to invoke
    given the info dictionary and the specific information (names,versions,
    licenses or src_urls) to look up, return the list of information'''
    if 'invoke' in info_dict[info]:
        info_list = process_base_invoke(info_dict[info]['invoke'],
                                        image_tag_string,
                                        info_dict['shell'])
        info_list = info_list[:-1]
        if 'delimiter' in info_dict[info]:
            info_list = info_list.split(info_dict[info]['delimiter'])
            if info_list[-1] == '':
                info_list.pop()
    else:
        info_list = info_dict[info]
    return info_list


def print_info_list(info_dict, info):
    '''Return a string with the corresponding information
    info is either 'names', 'versions', 'licenses' or 'src_urls'
    '''
    report = ''
    if 'invoke' in info_dict[info]:
        report = report + info + ':\n'
        for step in range(1, len(info_dict[info]['invoke'].keys()) + 1):
            if 'container' in info_dict[info]['invoke'][step]:
                report = report + '\tin container:\n'
                for snippet in info_dict[info]['invoke'][step]['container']:
                    report = report + '\t' + snippet
    else:
        for value in info_dict[info]:
            report = report + ' ' + value
    report = report + '\n'
    return report


def print_image_info(base_image_tag):
    '''Given the base image and tag in a tuple return a string containing
    the command_lib/base.yml'''
    info = cmds.get_base_info(base_image_tag)
    report = ''
    report = report + print_info_list(info, 'names')
    report = report + print_info_list(info, 'versions')
    report = report + print_info_list(info, 'licenses')
    report = report + print_info_list(info, 'src_urls')
    report = report + '\n'
    return report


def get_packages_from_base(base_image_tag):
    '''Get a list of package objects from invoking the commands in the
    command library base section:
        1. For the image and tag name find if there is a list of package names
        2. If there is an invoke dictionary, invoke the commands
        3. Create a list of packages'''
    pkg_list = []
    info = cmds.get_base_info(base_image_tag)
    image_tag_string = get_image_tag_string(base_image_tag)
    if info:
        names = get_info_list(info, 'names', image_tag_string)
        versions = get_info_list(info, 'versions', image_tag_string)
        licenses = get_info_list(info, 'licenses', image_tag_string)
        src_urls = get_info_list(info, 'src_urls', image_tag_string)
        if names and len(names) > 1:
            for index in range(0, len(names)):
                pkg = Package(names[index])
                if len(versions) == len(names):
                    pkg.version = versions[index]
                if len(licenses) == len(names):
                    pkg.license = licenses[index]
                if len(src_urls) == len(names):
                    pkg.src_url = src_urls[index]
                pkg_list.append(pkg)
        else:
            print(cannot_retrieve_base_packages.format(
                image=base_image_tag[0], tag=base_image_tag[1]))
    else:
        print(no_image_tag_listing.format(image=base_image_tag[0],
                                          tag=base_image_tag[1]))
    return pkg_list


def get_base_obj(base_image_tag):
    '''Get a list of layers with their associated packages:
        1. Check if the base image exists on the host machine
        2. Get the layers
        3. For each layer check if there is a list of packages associated
        with it in the cache
        4. If there are no packages return a list of empty layer objects'''
    obj_list = []
    if not check_base_image(base_image_tag):
        # the base image cannot be found locally nor remotely
        # at this point there is no context for Tern to use so raise an
        # exception to exit gracefully
        print(base_image_not_found)
        raise
    else:
        cache.load()
        # get the history with diff ids
        # tuples look like this: (history command, diff_id)
        layer_history = get_layer_history(get_image_tag_string(
            base_image_tag))
        for layer_tuple in layer_history:
            layer = Layer(layer_tuple[1])
            package_list = cache.get_packages(layer_tuple[1])
            for package in package_list:
                pkg_obj = Package(package['name'])
                pkg_obj.fill(package)
                layer.add(pkg_obj)
            obj_list.append(layer)
    return obj_list


def get_dockerfile_image_tag():
    '''Return the image and tag used to build an image from the dockerfile'''
    image_tag_string = cmds.image + df.tag_separator + cmds.tag
    return image_tag_string


def is_build():
    '''Attempt to build a given dockerfile
    If it does not build return False. Else return True'''
    image_tag_string = get_dockerfile_image_tag()
    success = False
    msg = ''
    try:
        cmds.build_container(dockerfile, image_tag_string)
    except subprocess.CalledProcessError as error:
        print(docker_build_failed.format(dockerfile=dockerfile,
                                         error_msg=error.output))
        success = False
        msg = error.output
    else:
        success = True
    return success, msg


def get_dockerfile_packages():
    '''Given the dockerfile commands get packages that may have been
    installed. Use this when there is no image or if it cannot be
    built
    1. For each RUN directive get the command used and the packages
    installed with it
    2. All of the packages that are recognized would be unconfirmed
    because there is no container to run the snippets against
    All the unrecognized commands will be returned as is
    Since there will be nothing more to do - recognized is just a list
    of packages that may have been installed in the dockerfile'''
    pkg_dict = cmds.remove_uninstalled(cmds.get_package_listing(
        docker_commands))
    recognized_list = []
    for command in pkg_dict['recognized'].keys():
        recognized_list.extend(pkg_dict['recognized'][command])
    pkg_dict.update({'recognized': recognized_list})
    return pkg_dict


def record_layer(layer_obj, package_list=[]):
    '''Given a layer object with a list of packages, record the layer in
    the cache without recording duplicate packages'''
    # get a list of package names in the current layer object
    pkg_names = []
    for pkg in layer_obj.packages:
        pkg_names.append(pkg.name)
    for pkg in package_list:
        if pkg.name not in pkg_names:
            layer_obj.add(pkg)
    cache.add_layer(layer_obj)


def build_layer_obj(sha, pkg_obj_list=[]):
    '''Create a layer object given the sha and a list of package objects'''
    layer_obj = Layer(sha)
    for pkg in pkg_obj_list:
        layer_obj.add(pkg)
    return layer_obj


def save_cache():
    cache.save()


def check_for_unique_package(package_list, package_name):
    '''In the snippet library the command name has a list of packages that can
    be installed with that command. A package name called 'default' indicates
    that the method of retrieving information applies to any package.
    However if there is an element with a specific name, the default is
    overridden with that name.
    Given a list of package dictionaries, find the package dictionary with the
    given package name. If not there look for a pacakge dictionary with the
    name as 'default'. If that is not there, return an empty dictionary'''
    pkg = {}
    for package in package_list:
        if package['name'] == package_name:
            pkg = package
            break
    if not pkg:
        for package in package_list:
            if package['name'] == 'default':
                pkg = package
                break
    return pkg


def get_package_dependencies(command_name, package_name, shell):
    '''Given the command name, the package name and the shell,
    find the list of dependencies'''
    deps = []
    # look up snippet library
    pkg_list = cmds.command_lib['snippets'][command_name]['packages']
    pkg_dict = check_for_unique_package(pkg_list, package_name)
    if pkg_dict and 'deps' in pkg_dict.keys():
        deps.extend(cmds.get_pkg_attr_list(shell, pkg_dict['deps'],
                                           package_name=package_name))
    return deps


def get_confirmed_packages(docker_run_inst, shell):
    '''For a dockerfile run instruction which is a tuple of type:
        ('RUN', command)
    1. Get the packages that were installed
    This is in the form of a dictionary that looks like this:
        instruction: <dockerfile instruction>
        recognized: {command_name: [list of installed packages], ...}
        unrecognized: [list of commands in the docker RUN instruction]
    2. Get the dependencies for each of the packages that were installed
    Update the dictionary to move the recognized to confirmed with a
    unique list of packages. The resulting dictionary looks like this:
        instruction: <dockerfile instruction>
        recognized: {command_name: [], ...}
        confirmed: {command_name: [],...}
        unrecognized: [list of commands in the docker RUN instruction]'''
    # get the instruction, the recognized packages and unrecognized commands
    run_dict = cmds.remove_uninstalled(
        cmds.get_packages_per_run(docker_run_inst))
    run_dict.update({'confirmed': {}})
    # get package dependencies
    for cmd in run_dict['recognized'].keys():
        cmd_dict = {cmd: []}
        all_pkgs = []
        remove_pkgs = []
        for pkg in run_dict['recognized'][cmd]:
            try:
                deps = get_package_dependencies(cmd, pkg, shell)
                all_pkgs.append(pkg)
                all_pkgs.extend(deps)
                remove_pkgs.append(pkg)
            except:
                print("Could not retireve dependencies for: " + pkg)
                pass
        cmd_dict[cmd].extend(list(set(all_pkgs)))
        run_dict['confirmed'].update(cmd_dict)
        for rem in remove_pkgs:
            run_dict['recognized'][cmd].remove(rem)
    return run_dict


def get_package_obj(command_name, package_name, shell):
    '''Given the command name, and the package name, retrieve the package
    information, create an oject and return the package object'''
    # look up command name in snippet library
    if command_name in cmds.command_lib['snippets'].keys():
        # get the unique or default information
        pkg_list = cmds.command_lib['snippets'][command_name]['packages']
        pkg_info = check_for_unique_package(pkg_list, package_name)
        if pkg_info:
            pkg = Package(package_name)
            # get the information for values
            keys = pkg_info.keys()
            if 'version' in keys:
                try:
                    version = cmds.get_pkg_attr_list(
                        shell, pkg_info['version'],
                        package_name=package_name)[0]
                    pkg.version = version
                except subprocess.CalledProcessError as error:
                    print(error.output)
            if 'license' in keys:
                try:
                    license = cmds.get_pkg_attr_list(
                        shell, pkg_info['license'],
                        package_name=package_name)[0]
                    pkg.license = license
                except subprocess.CalledProcessError as error:
                    print(error.output)
            if 'src_url' in keys:
                try:
                    src_url = cmds.get_pkg_attr_list(
                        shell, pkg_info['src_url'],
                        package_name=package_name)[0]
                    pkg.src_url = src_url
                except subprocess.CalledProcessError as error:
                    print(error.output)
            return pkg
        else:
            print(
                'No package named {} nor default listing'.format(package_name))
    else:
        print('No command {} listed in snippet library'.format(command_name))


def get_packages_from_snippets(command_dict, shell):
    '''Command dictionary looks like this:
        { command: [list of packages], command: [list of packages]...}
    This is the result of parsing through a Dockerfile RUN command.
    Return a list of packages objects that are installed from the Dockerfile
    RUN command'''
    package_list = []
    for cmd in command_dict.keys():
        for pkg in command_dict[cmd]:
            pkg_obj = get_package_obj(cmd, pkg, shell)
            package_list.append(pkg_obj)
    return package_list


def get_layer_history(image_tag_string):
    '''For an available image, get a list of tuples containing the dockerfile
    instruction that created the layer and the diff id of that layer'''
    history_list = []
    # save the image first
    if not cmds.extract_image_metadata(image_tag_string):
        # there was some error in extracting the metadata so we cannot
        # find the context for the base image
        print(cannot_extract_base_image)
        raise
    else:
        # get the list of non-empty history
        config = meta.get_image_config()
        history = meta.get_nonempty_history(config)
        diff_ids = meta.get_diff_ids(config)
        # create a list of tuples
        for index in range(0, len(history)):
            history_list.append((history[index], diff_ids[index]))
    return history_list
