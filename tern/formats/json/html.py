# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

from tern.utils import general

def get_version():
    '''Return the version string for the --version command line option'''
    ver_type, commit_or_ver = general.get_git_rev_or_version()
    message = ''
    if ver_type == "package":
        message = "Tern version {}".format(commit_or_ver)
    else:
        message = "Tern at commit {}".format(commit_or_ver)
    return message

def print_licenses_only(image_obj_list):
    '''Print a complete list of licenses for all images'''
    full_license_list = []
    for image in image_obj_list:
        for layer in image.layers:
            for package in layer.packages:
                if (package.pkg_license and
                        package.pkg_license not in full_license_list):
                    full_license_list.append(package.pkg_license)

            for f in layer.files:
                for license_expression in f.license_expressions:
                    if license_expression not in full_license_list:
                        full_license_list.append(license_expression)
    return full_license_list


css ='''
<style>
ul, #myUL {
  list-style-type: circle;
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
  text-decoration: underline;
  font-family: 'Oswald', sans-serif;
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
</style>\n
'''

js= ''' 
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
<link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@300&family=Oswald&display=swap" rel="stylesheet"> 
<link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:ital,wght@1,300&display=swap" rel="stylesheet"> 
%s \n
</head>
<body>
<div class="header">
<img src="https://raw.githubusercontent.com/tern-tools/tern/master/docs/img/tern_logo.png" height="60px">\n
<br>
</div>\n
<div style="font-family: 'Josefin Sans', sans-serif;">
<p>
%s
<p>
The following report was generated for "%s" image.
</div>
"""
def image_handler(listObj, indent, file):
    for i in listObj:
      dictHandler(i,indent+1,file)

def dictHandler(dictObj, indent, file):
    file.write('  '*indent + '<ul class ="nested"> \n')
    for k,v in dictObj.items():
        if isinstance(v, dict):
            if "name" in v.keys():
                file.write('  '*indent + '<li><span class="caret">' +str(v["name"])+ ' : ' + '</span> \n ')
            else:
                file.write('  '*indent + '<li><span class="caret">' +str(k)+ ' : ' + '</span> \n ')
            dictHandler(v, indent+1,file)
            file.write('  '*indent + '</li> \n ')
        elif isinstance(v, list):
            if k == "images":
                file.write('  '*indent + '<li><span class="caret">' +str(k)+ ' : ' + '[%d]'%(len(v))+ '</span> \n ')
                image_handler(v,indent,file)
                file.write('  '*indent + '</li>\n')
            else:
                file.write('  '*indent + '<li><span class="caret">' +str(k)+ ' : ' + '[%d]'%(len(v))+ '</span> \n ')
                file.write('  '*indent + '<ul class ="nested"> \n ')
                listHandler(v, indent+1,file)
                file.write('  '*indent + '</ul> \n '+'  '*indent + '</li> \n ')
        else:
            file.write(' '*indent  + '<li><span >' + str(k) + ' : ' + '</span><span style="color:green;font-family: \'Inconsolata\', monospace;">' +str(v)+  ' </span></li> \n ')
    file.write('  '*indent + '</ul> \n ')

def listHandler(listObj, indent, file):
    for i in range(len(listObj)):
        if isinstance(listObj[i], dict):
            if "name" in listObj[i].keys():
                file.write('  '*indent + '<li><span class="caret">' +str(listObj[i]["name"])+ ' : '+ '</span> \n ')
            else:  
                file.write('  '*indent + '<li><span class="caret">' +str(i)+ ' : '+'</span> \n ')
            dictHandler(listObj[i], indent+1, file)
            file.write('  '*indent + '</li> \n ')
        elif isinstance(listObj[i], list):
            file.write('  '*indent + '<li><span class="caret">' +str(i)+ ' : '+ '</span> \n ')
            file.write('  '*indent + '<ul class ="nested"> \n ')
            listHandler(listObj[i],indent+1,file)
            file.write('  '*indent + '</ul> \n '+'  '*indent + '</li>\n ')
        else:
            file.write(' '*indent  + '<li>'+ '<span style="color:green;font-family: \'Inconsolata\' , monospace;">' +str(listObj[i])+ '</span>\n</li> \n ')

def write_licenses(image_obj_list,file):
    licenses = print_licenses_only(image_obj_list)
    file.write('<ul class ="myUL"> \n')
    file.write('<li><span class="caret">Summary of Licenses Found</span> \n')
    file.write('<ul class ="nested"> \n')
    for l in licenses:
      file.write('<li style="font-family: \'Inconsolata\' , monospace;" >'+l+'</li>\n')
    file.write('</ul></li></ul> \n')

def json_to_html(report, file):
    file.write('<ul class ="myUL"> \n')
    file.write('<li><span class="caret">REPORT</span> \n')
    dictHandler(report, 0, file)
    file.write('</li></ul> \n')

def create_html(report,image_obj_list,args,filename = "report.html"):
    with open(filename+".html","w+") as f:
        f.write(head%(css,get_version(),args.docker_image))
        write_licenses(image_obj_list,f)
        json_to_html(report, f)
        f.write(js)
        f.write("</body>\n</html>\n")

