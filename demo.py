'''
Docker compliance tool demo

Objectives for first pass:
    Given a Dockerfile used to build a Docker image, produce a report
    containing all of the installed packages with the source locations
'''

import argparse

from utils import dockerfile as df
from utils import commands as cmds
import report as r


def main(dockerfile):
    '''Given a Dockerfile do the following:
        1. Get the base image and tag
        2. Find all the packages that are installed that are in the
        command library
        3. If there are any retrieval steps execute those
        4. Write a report'''
    docker_commands = df.get_directive_list(df.get_command_list(dockerfile))
    base_image_tag = df.get_base_image_tag(
        df.get_base_instructions(docker_commands))
    # for now the image that gets build will be tagged with an image name
    # and the name of the base image on which it is being built
    # The image name is in commands.py
    image_tag_string = cmds.image + df.tag_separator + base_image_tag[0]
    packages = cmds.get_packages(docker_commands)
    # for now remove all the packages that possibly got uninstalled
    packages['recognized'] = cmds.remove_uninstalled(packages['recognized'])
    packages['unrecognized'] = cmds.remove_uninstalled(
        packages['unrecognized'])
    # create a package dictionary to report
    report = {}
    report.update({'recognized': {'packages': []},
                   'unrecognized': {'packages': []}})
    # fill out recognized
    for command in packages['recognized'].keys():
        if cmds.check_all_pkgs(command):
            # in this case there is probably a url retrieval step
            # we can start a container here
            cmds.start_container(dockerfile, image_tag_string)
            # we can get the url retrieval step here
            pkg_rules = cmds.command_lib[command]['packages'][0]
            if 'url_retrieval' in pkg_rules.keys():
                for pkg in packages['recognized'][command]:
                    pkg_dict = {'name': pkg}
                    # TODO: allow for commands invoked on the host machine
                    if 'container' in pkg_rules['url_retrieval'].keys():
                        invoke = pkg_rules[
                            'url_retrieval']['container']['invoke']
                        results = cmds.invoke_in_container(
                            invoke, pkg, image_tag_string)
                        pkg_dict.update({'url': results})
                    report['recognized']['packages'].append(pkg_dict)
            cmds.remove_container()
            cmds.remove_image(image_tag_string)
    # fill out all the unrecognized packages
    report['unrecognized']['packages'] = packages['unrecognized']
    report_str = r.record_report(report)
    r.write_report(report_str)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dockerfile')
    args = parser.parse_args()
    main(args.dockerfile)
