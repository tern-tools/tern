![Tern](/docs/img/tern_logo.png)

# Welcome to the Tern Project

Tern is an inspection tool to find the metadata of the packages installed in a container image. It runs scripts from the "command library" against the container and collates the information into a Bill of Materials (BOM) report. Tern gives you a deeper understanding of your container's bill of materials so you can make better decisions about your container based infrastructure, integration and deployment strategies.

## Why Tern?
Tern was created to help developers meet open source compliance requirements for containers. Tools like Docker make it easy to build and distribute containers but keeping track of what is installed in the container is left to dev or devops teams. Knowing your container's Bill of Materials not only helps you meet your open source compliance obligations, but helps you debug integration and build errors and identify vulnerable packages in your running containers easily.

## Table of Contents
- [Getting Started](#getting-started)
- [Project Status](#project-status)
- [Documentation](#documetation)
- [Contributing](#contributing)
- [Glossary of Terms](/docs/glossary.md)
- [Architecture](/docs/architecture.md)
- [Navigating the Code](/docs/navigating-the-code.md)

## Getting Started<a name="getting-started"/>

### Requirements
Tern is currently developed on a Linux distro with a kernel version >= 4.0. Possible development distros are Ubuntu 16.04 or newer or Fedora 25 or newer.
Install the following:
- Git (Installation instructions can be found here: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Python 3.6.2 (sudo apt-get install python3.6 or sudo dnf install python36)

If you happen to be using Docker containers
- Docker CE (Installation instructions can be found here: https://docs.docker.com/engine/installation/#server)

Make sure the docker daemon is running.


```
$ python3 -m venv ternenv
$ cd ternenv
$ git clone https://github.com/vmware/tern.git
$ source bin/activate
$ cd tern
$ pip install -r requirements.txt
$ ./tern report -d samples/photon_git/Dockerfile
```

Take a look at report.txt to see what packages are installed in the created Docker image and how Tern got this information. Feel free to try this out on the other sample Dockerfiles in the samples directory or on Dockerfiles you may be working with.

### To get a summary report
```
$ ./tern report -s -d samples/photon_git_Dockerfile
```
WARNING: Tern is meant to give guidance on what may be installed for each line in a Dockerfile so it is recommended that for the purpose of investigation, the default report is used. The summary report may be used as the output of a build artifact or something to submit to a compliance or legal team.

### To run a test
```
$ cd ternenv
$ source bin/activate
$ git clone https://github.com/vmware/tern.git
$ cd tern
$ export PYTHONPATH=`pwd`
$ python tests/<test file>.py
```
## Project Status<a name="project-status"/>

Tern currently has these features:
* A Cache to store layers with the packages that are installed in those layers
* A report containing a line-by-line 'walkthrough' of the Dockerfile to say what packages were installed in each line
* A summary report
* The complete list of dependencies are retrieved

Current work:
* Code refactoring
* Layering of container filesystems one by one
* Source retrieval

## Documentation<a name="documentation"/>
Architecture, function blocks, code descriptions and the project roadmap are located in the docs folder. We also welcome contributions to the documentation. See the [contributing guide](/CONTRIBUTING.md) to find out how to submit changes.

## Get Involved<a name="contributing"/>

Do you have questions about Tern? Do you think it can do better? Would you like to make it better? You can get involved by giving your feedback and contributing to the code, documentation and conversation!

Please read our [code of conduct](/CODE_OF_CONDUCT.md) first.

Next, take a look at the [contributing guide](/CONTRIBUTING.md) to find out how you can start.
