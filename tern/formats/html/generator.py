# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

"""
HTML document generator
"""

import logging

from tern.formats import generator
from tern.report.content import get_tool_version, get_licenses_only
from tern.utils import constants


# global logger
logger = logging.getLogger(constants.logger_name)


css = '''
<style>
ul, #myUL {
  list-style-type: none;
}
li {
    padding-top: 5px;padding-bottom: 5px;
}
#myUL {
  margin: 0;
  padding: 0;
}
.caret {
  cursor: pointer;
  user-select: none;
  font-family: 'Inconsolata', monospace;
}
.caret::before {
  content: " \\25B6";
  color: ;
  display: inline-block;
margin-right: 6px;
}
.caret-down::before {
  transform: rotate(90deg);
}
.nested {
  display: none;
}
.active {
  display: block;
}
.header {
  text-align: left;
  background: #f1f1f1;
}
.text-c {
    color:green;
    font-family:'Inconsolata',monospace;
}
.text-h {
    font-family:'Inconsolata',monospace;
}
</style>\n
'''


js = '''
<script>
var toggler = document.getElementsByClassName("caret");
var i;
for (i = 0; i < toggler.length; i++) {
  toggler[i].addEventListener("click", function() {
    this.parentElement.querySelector(".nested").classList.toggle("active");
    this.classList.toggle("caret-down");
  });
}
</script>\n
'''


head = """
<!DOCTYPE html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@300&family=Oswald&display=swap"
rel="stylesheet"><link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@1,300&display=swap"
rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inconsolata&display=swap" rel="stylesheet">
%s \n
</head>
<body>
<div class="header">
<img src="https://raw.githubusercontent.com/tern-tools/tern/master/docs/img/tern_logo.png" height="60px">\n
<br>
</div>\n
<div style="font-family: \'Inconsolata\', monospace;">
<p>
Tern at %s
<p>
The following report was generated for "%s" image.
</div>
"""


def image_handler(list_obj, indent):
    '''Write html code for the images list in the report with
    image name as title'''
    html_string = ''
    for i in list_obj:
        html_string = html_string + dict_handler(i, indent+1)
    return html_string


def manifest_handler(list_obj, indent):
    '''Write html code for the manifests list in the report
    with config as title'''
    html_string = '  '*indent + '<ul class ="nested"> \n'
    for lo in list_obj:
        html_string = html_string + '  '*indent + '<li><span class="caret">' \
            + str(lo["Config"][:10]) + ' : ' + '</span> \n '
        html_string = html_string + dict_handler(lo, indent+1)
        html_string = html_string + '  '*indent + '</li> \n'
    html_string = html_string + '  '*indent + '</ul> \n'
    return html_string


def layers_handler(list_obj, indent):
    '''Write html code for the origins list in the report
    with tar_file hash as title'''
    html_string = '  '*indent + '<ul class ="nested"> \n'
    for lo in list_obj:
        html_string = html_string + '  '*indent + '<li><span class="caret">' \
            + str(lo["tar_file"][:10]) + ' : ' + '</span> \n '
        html_string = html_string + dict_handler(lo, indent+1)
        html_string = html_string + '  '*indent + '</li> \n'
    html_string = html_string + '  '*indent + '</ul> \n'
    return html_string


def history_handler(list_obj, indent):
    '''Write html code for the history list in the report
    with time-stamp as title'''
    html_string = '  '*indent + '<ul class ="nested"> \n'
    for lo in list_obj:
        html_string = html_string + '  '*indent + '<li><span class="caret">' \
            + str(lo["created"][:19]) + ' : ' + '</span> \n '
        html_string = html_string + dict_handler(lo, indent+1)
        html_string = html_string + '  '*indent + '</li> \n'
    html_string = html_string + '  '*indent + '</ul> \n'
    return html_string


def origins_handler(list_obj, indent):
    '''Write html code for the origins list in the report
    with origin string as title'''
    html_string = '  '*indent + '<ul class ="nested"> \n'
    for lo in list_obj:
        html_string = html_string + '  '*indent + '<li><span class="caret">' \
            + str(lo["origin_str"]) + '</span> \n '
        html_string = html_string + dict_handler(lo, indent+1)
        html_string = html_string + '  '*indent + '</li> \n'
    html_string = html_string + '  '*indent + '</ul> \n'
    return html_string


def list_handler(list_obj, indent):
    '''Write html code for lists in report dictionary'''
    html_string = ''
    for i, _ in enumerate(list_obj):
        if isinstance(list_obj[i], dict):
            if "name" in list_obj[i].keys():
                html_string = html_string + '  '*indent + \
                    '<li><span class="caret">' + str(list_obj[i]["name"]) + \
                    ' : ' + '</span> \n '
            else:
                html_string = html_string + '  '*indent + \
                    '<li><span class="caret">' + str(i) + ' : ' + '</span> \n '
            html_string = html_string + dict_handler(list_obj[i], indent+1)
            html_string = html_string + '  '*indent + '</li> \n '
        elif isinstance(list_obj[i], list):
            html_string = html_string + '  '*indent + \
                '<li><span class="caret">' + str(i) + ' : ' + '</span> \n '
            html_string = html_string + '  '*indent + \
                '<ul class ="nested"> \n '
            html_string = html_string + list_handler(list_obj[i], indent+1)
            html_string = html_string + '  '*indent + '</ul> \n ' + \
                '  '*indent + '</li>\n '
        else:
            html_string = html_string + ' '*indent + '<li>' + \
                '<span class="text-c">' + str(list_obj[i]) + \
                '</span>\n</li> \n '
    return html_string


# pylint: disable=too-many-branches
def dict_handler(dict_obj, indent):
    '''Writes html code for dictionary in report dictionary'''
    html_string = ''
    html_string = html_string + '  '*indent + '<ul class ="nested"> \n'
    for k, v in dict_obj.items():
        if isinstance(v, dict):
            if "name" in v.keys():
                html_string = html_string + '  '*indent + \
                    '<li><span class="caret">' + str(v["name"]) + ' : ' + \
                    '</span> \n '
            else:
                html_string = html_string + '  '*indent + \
                    '<li><span class="caret">' + str(k) + ' : ' + '</span> \n '
            html_string = html_string + dict_handler(v, indent+1) + \
                '  '*indent + '</li> \n '
        elif isinstance(v, list):
            html_string = html_string + '  '*indent + \
                '<li><span class="caret">' + str(k) + ' : ' + \
                '[%d]' % (len(v)) + '</span> \n '
            if k == "images":
                html_string = html_string + image_handler(v, indent) + \
                    '  '*indent + '</li>\n'
            elif k == "manifest":
                html_string = html_string + manifest_handler(v, indent) + \
                    '  '*indent + '</li>\n'
            elif k == "layers":
                html_string = html_string + layers_handler(v, indent) + \
                    '  '*indent + '</li>\n'
            elif k == "origins":
                html_string = html_string + origins_handler(v, indent) + \
                    '  '*indent + '</li>\n'
            elif k == "history":
                html_string = html_string + history_handler(v, indent) + \
                    '  '*indent + '</li>\n'
            else:
                html_string = html_string + '  '*indent + \
                    '<ul class ="nested"> \n ' + list_handler(v, indent+1) + \
                    '  '*indent + '</ul> \n ' + '  '*indent + '</li> \n '
        else:
            html_string = html_string + ' '*indent + \
                '<li><span class="text-h">' + str(k) + ' : ' + \
                '</span><span class="text-c">' + str(v) + '</span></li>\n'
    html_string = html_string + '  '*indent + '</ul> \n '
    return html_string


def report_dict_to_html(dict_obj):
    '''Writes html code for report'''
    html_string = ''
    html_string = html_string + '<ul class ="myUL"> \n'
    html_string = html_string + \
        '<li><span class="caret">REPORT DETAILS</span> \n'
    html_string = html_string + dict_handler(dict_obj, 0)
    html_string = html_string + '</li></ul> \n'
    return html_string


def write_licenses(image_obj_list):
    '''Adds licenses to top of the page'''
    licenses = get_licenses_only(image_obj_list)
    html_string = ''
    html_string = html_string + '<ul class ="myUL"> \n'
    html_string = html_string + '<li><span class="caret">Summary of \
        Licenses Found</span> \n'
    html_string = html_string + '<ul class ="nested"> \n'
    for lic in licenses:
        html_string = html_string + \
            '<li style="font-family: \'Inconsolata\' , monospace;" >' + \
            lic + '</li>\n'
    html_string = html_string + '</ul></li></ul> \n'
    return html_string


def create_html_report(report_dict, image_obj_list):
    '''Return the html report as a string'''
    logger.debug("Creating HTML report...")
    report = ''
    report = report + '\n' + head % (css, get_tool_version(),
                                     report_dict['images'][0]['image']['name']
                                     + ':' +
                                     report_dict['images'][0]['image']['tag'])
    report = report + '\n' + write_licenses(image_obj_list)
    report = report + '\n' + report_dict_to_html(report_dict)
    report = report + '\n' + js
    report = report + '\n' + '</body>\n</html>\n'
    return report


def get_report_dict(image_obj_list):
    '''Given an image object list, return a python dict of the report'''
    image_list = []
    for image in image_obj_list:
        image_list.append({'image': image.to_dict()})
    image_dict = {'images': image_list}
    return image_dict


class HTML(generator.Generate):
    def generate(self, image_obj_list):
        '''Given a list of image objects, create a html report
        for the images'''
        report_dict = get_report_dict(image_obj_list)
        report = create_html_report(report_dict, image_obj_list)
        return report
