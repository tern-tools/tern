'''
Edit a report string and write it to a file
'''

# constants
report_file = 'sources.txt'
report_recog = 'Recognized sources:\n'
report_package = '\t{package_name}\n'
report_url = '\t\turl: {url}\n'
report_version = '\t\tversion: {version}\n'
report_unrecog = 'Unrecognized sources:\n'


def record_report(report_dict):
    '''The report dict will look like this:
        recognized:
            packages:[{name: <name>, url: <url>, version: <version>}...]
        unrecognized:
            packages:[<package names>]
    Record the report with each of these values'''
    report = report_recog
    for package in report_dict['recognized']['packages']:
        report = report + report_package.format(package_name=package['name'])
        if 'url' in package.keys():
            report = report + report_url.format(url=package['url'])
        if 'version' in package.keys():
            report = report + report_version.format(
                version=package['version'])
    report = report + report_unrecog
    for package in report_dict['unrecognized']['packages']:
        report = report + package + ' '
    return report


def write_report(report):
    '''Write the report to a file'''
    with open(report_file, 'w') as f:
        f.write(report)
