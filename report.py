'''
Create a report
'''
import logging

from utils.commands import start_container
from utils.commands import remove_container
from utils.commands import remove_image
import common

# constants
report_file = 'report.txt'
report_confirmed = 'Confirmed sources:\n'
report_unconfirmed = 'Unconfirmed sources:\n'
report_package = '\tpackage: {package}\n'
report_url = '\t\turl: {url}\n'
report_version = '\t\tversion: {version}\n'
report_license = '\t\tlicense: {license}\n'
report_unrecog = 'Unrecognized packages:\n'
report_notes = 'NOTES:\n'

# report messages
no_packages = '''Unable to recover packages for layer {layer}.
Consider either entering them manually or create a bash script to retrieve the
package in the command library.\n'''
no_version = '''No version for package {package}.
Consider either entering the version manually or creating a script to retrieve
it in the command library\n'''
no_license = '''No license for package {package}.
Consider either entering the license manually or creating a script to retrieve
it in the command library\n'''
no_src_url = '''No source url for package {package}.
Consider either entering the source url manually or creating a script to
retrieve it in the command library\n'''
env_dep_dockerfile = '''Docker build failed: {build_fail_msg} \n
Since the Docker image cannot be built, Tern will try to retrieve package
information from the Dockerfile itself.\n'''
invoking_from_base = '''
Checking against command_lib/base.yml to retrieve information about packages
in this layer. Some of the results are shell snippets that will be invoked\n'''
checking_against_snippets = '''
Checking against command_lib/snippets.yml to see if there is a listing for
the commands in the Dockerfile RUN line\n'''
retrieved_from_cache = '''\nThere is a record of layer {sha} in the cache.
Packages in the cache:\n'''
retrieved_by_invoke = '''\nRetrieving package information in layer {sha}
by running commands:\n'''
section_terminator = '''\n--------------------------------------------\n\n'''


def write_report(report):
    '''Write the report to a file'''
    with open(report_file, 'w') as f:
        f.write(report)


def print_package_notes(packages, report, notes):
    '''Append to the given report package information and notes if the
    information is missing'''
    report = report + section_terminator
    report = report + '\n'
    for package in packages:
        report = report + report_package.format(package=package.name)
        report = report + report_version.format(version=package.version)
        report = report + report_license.format(license=package.license)
        report = report + report_url.format(url=package.src_url)
        report = report + section_terminator
        if package.version == 0.0:
            notes = notes + no_version.format(package=package.name)
        if package.license == '':
            notes = notes + no_license.format(package=package.name)
        if package.src_url == '':
            notes = notes + no_src_url.format(package=package.name)
    return report, notes


def print_invoke_per_instruction(confirmed_command_dict):
    '''For each of the confirmed commands in a dockerfile run instruction,
    print all the invoked snippets'''
    report = ''
    for command in confirmed_command_dict.keys():
        for pkg in confirmed_command_dict[command]:
            report = report + common.print_package_info(command, pkg) + '\n'
    return report


def print_image_base(report, base_image_msg, layer_obj, pkg_name_list,
                     is_summary, logger):
    '''Given, the report string, the base image tuple with notes, the layer
    object, the collated package name list and whether we are writing a summary
    report or not, Return a report that contains the packages in the base
    image
    Check if the layer object has any package listing. If there is then
    create a report containing the content. If not then look up any snippets
    in the base command library'''
    # get package information for this layer
    if layer_obj.packages:
        # there was something in the cache
        logger.debug('Adding packages from cache from layer: {}'.format(
            layer_obj.sha[:10]))
        if is_summary:
            report, notes = print_package_notes(layer_obj.packages, report, '')
            report = report + section_terminator
        else:
            report = report + retrieved_from_cache.format(
                sha=layer_obj.sha[:10])
            report, notes = print_package_notes(
                layer_obj.packages, report, '')
            report = report + base_image_msg[1]
            report = report + notes
            report = report + section_terminator
    else:
        # nothing in the cache - check in the command library
        logger.debug('Nothing in cache for layer {}. \
                     Invoking from command library'.format(
                         layer_obj.sha[:10]))
        # start a container
        image_tag_string = common.get_image_tag_string(base_image_msg[0])
        start_container(image_tag_string)
        package_list = common.get_packages_from_base(base_image_msg[0])
        # remove container when done
        remove_container()
        remove_image(image_tag_string)
        if package_list:
            # put layer in cache
            common.record_layer(layer_obj, package_list)
            # add to master list
            common.collate_package_names(pkg_name_list, layer_obj)
            # append to report
            if is_summary:
                report, notes = print_package_notes(
                    layer_obj.packages, report, '')
            else:
                report = report + retrieved_by_invoke.format(
                    sha=layer_obj.sha[:10])
                report = report + common.print_image_info(base_image_msg[0])
                report, notes = print_package_notes(
                    layer_obj.packages, report, '')
                report = report + notes
                report = report + section_terminator
        else:
            if not is_summary:
                report = report + no_packages.format(layer=layer_obj.sha[:10])
    return report


def print_dockerfile_run(report, shell, base_layer_no, pkg_name_list,
                         is_summary, logger):
    '''Given the report, the shell used for commands in the built image
    and the number of base layers in the history, retrieve package
    information for each of the dockerfile RUN instructions and append the
    results to the report and return the report
    1. Retrieve the history and the diff ids for the built image and remove
    the first few lines corresponding to the base image. The next line should
    correspond with the first dockerfile line run
    2. For each Dockerfile RUN
        1. Check if the dockerfile run matches the history.
        If yes - that is the layer sha. If not, skip to the next RUN line
        2. Get the run dictionary of commands and packages that were installed
        with them
        3. Retrieve package information for these packages
        4. Create the layer object with this list
        5. Record the layer with package information
        6. Append to the report the Dockerfile line, and the packages retrieved
    '''
    layer_history = common.get_layer_history(common.get_dockerfile_image_tag())
    while base_layer_no > 0:
        layer_history.pop(0)
        base_layer_no = base_layer_no - 1
    for instr in common.docker_commands:
        if instr[0] == 'RUN':
            if instr[1] in layer_history[0][0]:
                # this is the sha for the given layer
                sha = layer_history[0][1]
                # retrieve the layer
                layer_obj = common.get_layer_obj(sha)
                if not is_summary:
                    report = report + instr[0] + ' ' + instr[1] + '\n'
                if layer_obj.packages:
                    # print out the packages
                    if is_summary:
                        report, notes = print_package_notes(
                            layer_obj.packages, report, '')
                    else:
                        report = report + retrieved_from_cache.format(
                            sha=layer_obj.sha[:10])
                        report, notes = print_package_notes(
                            layer_obj.packages, report, '')
                        report = report + notes
                        report = report + section_terminator
                else:
                    # see if we can get any from the snippet library
                    run_dict = common.get_confirmed_packages(
                        instr, shell, pkg_name_list)
                    if not is_summary:
                        report = report + retrieved_by_invoke.format(
                            sha=layer_obj.sha)
                        report = report + print_invoke_per_instruction(
                            run_dict['confirmed'])
                    pkg_list = common.get_packages_from_snippets(
                        run_dict['confirmed'], shell)
                    if pkg_list:
                        # put layer in cache
                        common.record_layer(layer_obj, pkg_list)
                        # append to master list
                        common.collate_package_names(pkg_name_list, layer_obj)
                        # append to report
                        if is_summary:
                            report, notes = print_package_notes(
                                layer_obj.packages, report, '')
                        else:
                            report, notes = print_package_notes(
                                layer_obj.packages, report, '')
                            report = report + notes
                            report = report + section_terminator
                    else:
                        if not is_summary:
                            report = report + no_packages.format(
                                layer=layer_obj.sha)
    return report


def execute(args):
    '''
    Create a report like this:
        1. The lines from the Dockerfile
        2. What the tool is doing (either getting package information
        from the cache or command library
        3. The list of packages
        4. Any issues that were detected or suggestions to change the
        Dockerfile or Command Library
    For summary, print
        1. The lines from the Dockerfile
        2. The packages that came from that line
        '''
    report = ''
    logger = logging.getLogger('ternlog')
    if args.dockerfile:
        # parse the dockerfile
        common.load_docker_commands(args.dockerfile)
    # master list of package names so far
    master_list = []

    # ----------------------------------------------------
    # Step 1: Get the packages installed in the base image
    # ----------------------------------------------------
    if not args.summary:
        report = report + common.print_dockerfile_base()
    base_image_msg = common.get_dockerfile_base()
    # get a list of packages that are installed in the base image
    # the list may contain some layers with no packages in it because
    # there may be no record of them in the cache
    base_obj_list = common.get_base_obj(base_image_msg[0])
    for layer_obj in base_obj_list:
        report = print_image_base(
            report, base_image_msg, layer_obj, master_list, args.summary,
            logger)

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
