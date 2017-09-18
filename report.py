'''
Create a report
'''
import sys

import common

# constants
report_file = 'report.txt'
report_confirmed = 'Confirmed sources:\n'
report_unconfirmed = 'Unconfirmed sources:\n'
report_package = '\t{package_name}\n'
report_url = '\t\turl: {url}\n'
report_version = '\t\tversion: {version}\n'
report_license = '\t\tlicense:\n {license}\n'
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


def record_report(report_dict):
    '''The report dict will look like this:
        confirmed: [{name: <name>, url: <url>, version: <version>}...]
        unconfirmed:[{name: <name>, url: <url>, version: <version>}...]
        unrecognized: [<package names>]
    Record the report with each of these values
    If there are no packages, record nothing'''
    report = report_confirmed
    if report_dict['confirmed']:
        for package in report_dict['confirmed']:
            report = report + report_package.format(
                package_name=package['name'])
            report = report + report_url.format(url=package['src_url'])
            report = report + report_version.format(version=package['version'])
            report = report + report_license.format(license=package['license'])
    report = report + report_unconfirmed
    if report_dict['unconfirmed']:
        for package in report_dict['unconfirmed']:
            report = report + report_package.format(
                package_name=package['name'])
            report = report + report_url.format(url=package['src_url'])
            report = report + report_version.format(version=package['version'])
            report = report + report_license.format(license=package['license'])
    report = report + report_unrecog
    if report_dict['unrecognized']:
        for name in report_dict['unrecognized']:
            report = report + name + ' '
    return report


def write_report(report):
    '''Write the report to a file'''
    with open(report_file, 'w') as f:
        f.write(report)


def append_report(packages, report, notes):
    '''Append the report and notes with packaging information'''
    for package in packages:
        report['confirmed'].append(package.to_dict())
        if package.version == 0.0:
            notes = notes + no_version.format(package=package.name)
        if package.license == '':
            notes = notes + no_license.format(package=package.name)
        if package.src_url == '':
            notes = notes + no_src_url.format(package=package.name)
    return report, notes


def execute(args):
    '''Create a report:
    TODO: need to get the list of packages from the rest of the
    Dockerfile'''
    report = {}
    notes = ''
    report.update({'confirmed': [], 'unconfirmed': [], 'unrecognized': []})
    if args.dockerfile:
        # parse the dockerfile
        common.load_docker_commands(args.dockerfile)
    base_image_msg = common.get_dockerfile_base()
    notes = notes + base_image_msg[1]
    # get the list of layers in the base image
    base_obj_list = common.get_base_obj(base_image_msg[0])
    for base_obj in base_obj_list:
        if base_obj.packages:
            report, notes = append_report(base_obj.packages, report, notes)
        else:
            # see if packages can be extracted
            # TODO: right now it is with the whole base image only
            # i.e. they have only one layer
            package_list = common.get_packages_from_snippets(base_image_msg[0])
            if package_list:
                report, notes = append_report(package_list, report, notes)
            else:
                notes = notes + no_packages.format(layer=base_obj.sha)

    report_txt = record_report(report) + '\n\n'
    report_txt = report_txt + report_notes + notes
    write_report(report_txt)
    sys.exit(0)
