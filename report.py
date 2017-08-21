'''
Create a report
'''
# import sys

import common

# constants
report_file = 'report.txt'
report_confirmed = 'Confirmed sources:\n'
report_unconfirmed = 'Unconfirmed sources:\n'
report_package = '\t{package_name}\n'
report_url = '\t\turl: {url}\n'
report_version = '\t\tversion: {version}\n'
report_unrecog = 'Unrecognized packages:\n'


def record_report(report_dict):
    '''The report dict will look like this:
        confirmed: [{name: <name>, url: <url>, version: <version>}...]
        unconfirmed:[{name: <name>, url: <url>, version: <version>}...]
        unrecognized: [<package names>]
    Record the report with each of these values'''
    report = report_confirmed
    for package in report_dict['confirmed']:
        report = report + report_package.format(package_name=package['name'])
        report = report + report_url.format(url=package['url'])
        report = report + report_version.format(version=package['version'])
    report = report + report_unconfirmed
    for package in report_dict['unconfirmed']:
        report = report + report_package.format(package_name=package['name'])
        report = report + report_url.format(url=package['url'])
        report = report + report_version.format(version=package['version'])
    report = report + package + ' '
    return report


def write_report(report):
    '''Write the report to a file'''
    with open(report_file, 'w') as f:
        f.write(report)


def execute(args):
    '''Create a report'''
    if args.dockerfile:
        # parse the dockerfile
        common.load_docker_commands(args.dockerfile)
