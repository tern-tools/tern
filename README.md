![Tern](/docs/img/tern_logo.png)

[![GitHub Actions](https://github.com/tern-tools/tern/workflows/Pull%20Request%20Lint%20and%20Test/badge.svg?branch=master)](https://github.com/tern-tools/tern/actions)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2689/badge)](https://bestpractices.coreinfrastructure.org/projects/2689)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

# Welcome to the Tern Project

Tern is a software package inspection tool for containers. It's written in Python3 with a smattering of shell scripts.

# Table of Contents
- [Introduction](#what-is-tern)
  - [FAQ](/docs/faq.md)
  - [Glossary of Terms](/docs/glossary.md)
  - [Architecture](/docs/architecture.md)
  - [Navigating the Code](/docs/navigating-the-code.md)
  - [Data Model](/docs/data-model.md)
- [Getting Started](#getting-started)
  - [Getting Started on Linux](#getting-started-on-linux)
  - [Getting Started with Docker](#getting-started-with-docker)
  - [Getting Started with Vagrant](#getting-started-with-vagrant)
- [Using Tern](#using-tern)
  - [Generating an SBoM report for a Docker image](#sbom-for-docker-image)
  - [Generating an SBoM report from a Dockerfile](#sbom-for-dockerfile)
  - [Generating a locked Dockerfile](#dockerfile-lock)
- [Report Formats](#report-formats)
  - [Human Readable Format](#report-human-readable)
  - [JSON Format](#report-json)
  - [HTML Format](#report-html)
  - [YAML Format](#report-yaml)
  - [SPDX tag-value Format](#report-spdxtagvalue)
- [Extensions](#extensions)
  - [Scancode](#scancode)
  - [cve-bin-tool](#cve-bin-tool)
- [Running tests](#running-tests)
- [Project Status](#project-status)
- [Contributing](/CONTRIBUTING.md)
  - [Code of Conduct](/CODE_OF_CONDUCT.md)
  - [Creating Report Formats](/docs/creating-custom-templates.md)
  - [Creating Tool Extensions](/docs/creating-tool-extensions.md)
  - [Adding to the Command Library](/docs/adding-to-command-library.md)

# What is Tern?<a name="what-is-tern">
Tern is an inspection tool to find the metadata of the packages installed in a container image. The overall operation looks like this:
1. It uses overlayfs to mount the first filesystem layer (also known as the BaseOS) used to build the container image
2. It then executes scripts from the "command library" in a chroot environment to collect information about packages installed in that layer
3. With that information as a starting point, it continues to iterate over steps 1 and 2 for the rest of the layers in the container image
4. Once done, it generates a report, various format options are available. The report, in its default format, provides a verbose, layer by layer, explanation of the various software components imported. If a Dockerfile is provided, the report indicates the Dockerfile lines corresponding to each of the file system layers.

Tern gives you a deeper understanding of your container's bill of materials so you can make better decisions about your container based infrastructure, integration and deployment strategies. It's also a good tool if you are curious about the contents of the container images you have built.

![Tern quick demo](/docs/img/tern_demo_fast.gif)


# Getting Started<a name="getting-started"/>

## Getting Started on Linux<a name="getting-started-on-linux">
If you have a Linux OS you will need a distro with a kernel version >= 4.0 (Ubuntu 16.04 or newer or Fedora 25 or newer are good selections) and will need to install the following requirements:

- Git (Installation instructions can be found here: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- attr (sudo apt-get install attr or sudo dnf install attr)
- Python 3.6 or newer (sudo apt-get install python3.6(3.7) or sudo dnf install python36(37))
- Pip (sudo apt-get install python3-pip).

Some distro versions have all of these except `attr` preinstalled but `attr` is a common utility and is available via the package manager.

For Docker containers
- Docker CE (Installation instructions can be found here: https://docs.docker.com/engine/installation/#server)

Make sure the docker daemon is running.

Create a python3 virtual environment:
```
$ python3 -m venv ternenv
$ cd ternenv
```

*NOTE:* Your OS might distribute each Python version separately. For example, on Ubuntu LTS, Python 2.7 is linked to `python2` and Python 3.6 is linked to `python3`. I develop with Python 3.7 which is installed separately with no symlinks. In this case, I use the binary. The binaries are usually installed in `/usr/bin/python`.

Activate the virtual environment:
```
$ source bin/activate
```
NOTE: This specific activate script only works for Bash shells. If you need to activate a Fish Shell or C Shell you should use `source bin/activate.fish` or `source bin/activate.csh`, respectively.

Install tern:
```
$ pip install tern
```

Run Tern:
```
$ tern report -o output.txt -i debian:buster
```

## Getting Started with Docker<a name="getting-started-with-docker">
Docker is the most widely used tool to build and run containers. If you already have Docker installed, you can run Tern by building a container with the Dockerfile provided and the `docker_run.sh` script:

Clone this repository:
```
$ git clone https://github.com/tern-tools/tern.git
```

Build the Docker image (called `ternd` here). You may need to use sudo:
```
$ docker build -t ternd .
```

**NOTE**: By default, Tern will run with logging turned on. If you would like to silent the terminal output when running the ternd container, make the following change to the Dockerfile ENTRYPOINT before building:

```
--- a/Dockerfile
+++ b/Dockerfile
-ENTRYPOINT ["tern", "--driver", "fuse"]
+ENTRYPOINT ["tern", "-q", "--driver", "fuse"]
```

Run the script `docker_run.sh`. You may need to use sudo. In the below command `debian` is the docker hub container image name  and `buster` is the tag that identifies the version we are interested in analyzing.

```
$ ./docker_run.sh ternd "report -i debian:buster" > output.txt
```

To produce a json report run
```
$ ./docker_run.sh ternd "report -f json -i debian:buster"
```

What the `docker_run.sh` script does is run the built container as privileged.

*WARNING:* privileged Docker containers are not secure. DO NOT run this container in production unless you have secured the node (VM or bare metal machine) that the docker daemon is running on.

Tern is not distributed as Docker images yet. This is coming soon. Watch the [Project Status](#project-status) for updates.

## Getting Started with Vagrant<a name="getting-started-with-vagrant">
Vagrant is a tool to setup an isolated virtual software development environment. If you are using Windows or Mac OSes and want to run Tern from the command line (not in a Docker container) this is the best way to get started as Tern does not run natively in a Mac OS or Windows environment at this time.

### Install
Follow the instructions on the [VirtualBox](https://www.virtualbox.org/wiki/Downloads) website to download VirtualBox on your OS.

Follow the instructions on the website to install [Vagrant](https://www.vagrantup.com/downloads.html) for your OS. 

### Create a Vagrant environment
**NOTE**: The following steps will install the latest [PyPI release](https://pypi.org/project/tern/#history) version of Tern. If you want to install Tern from the tip of master, please instead follow "Setting up a development environment on Mac and Windows" in the [contributing guide](/CONTRIBUTING.md).

In your terminal app, run the following commands. 

Clone this repository:
```
$ git clone https://github.com/tern-tools/tern.git
```

Bring up the Vagrant box: 
```
$ cd tern/vagrant
$ vagrant up
```

SSH into the created VM: 
```
$ vagrant ssh
```

Run:
```
$ tern report -i debian:buster -o output.txt
```

# Using Tern<a name="using-tern">

*WARNING*: The CLI has changed since the last release. Visit [Tern's PyPI project page](https://pypi.org/project/tern/) to find the correct CLI options or just run `tern -h`.

Tern creates a report containing the Bill of Materials (BoM) of a container image, including notes about how it collects this information, and files for which it has no information about. Currently, Tern supports containers only built using Docker using image manifest version 2, schema 2. Docker image manifest version 2, schema 1 has been [deprecated](https://docs.docker.com/registry/spec/deprecated-schema-v1/) by Docker. Tern will support container images created using Docker version 19.03.0 or later. Docker is the most ubiquitous type of container image that exists so the project started with a focus on those. However, it is architected to support other images that closely follow the [OCI image spec](https://github.com/opencontainers/image-spec/blob/master/spec.md).

## Generating an SBoM report for a Docker image<a name="sbom-for-docker-image">
If you have a Docker image pulled locally and want to inspect it
```
$ tern report -i debian:jessie
```
The SBoM of packages that are installed in the Docker image and how Tern got this information will be printed to the console. To direct this output to a file, use the `-o file_name` command line option. If you encounter any errors, please file an issue.

## Generating an SBoM report from a Dockerfile<a name="sbom-for-dockerfile">
You can provide a Dockerfile to Tern to figure out the Software Bill of Materials and other information. Tern will build the image, analyze it with respect to the Dockerfile and discard the image. This is useful to engineers who are developing a Dockerfile for their app or in a container build and release pipeline.
```
$ tern report -d samples/photon_git/Dockerfile
```
The SBoM of packages you would be shipping if you were to use the given Dockerfile will print to the console. To direct the output to a file, use the `-o file_name` command line option. Feel free to try this out on the other sample Dockerfiles in the samples directory or on Dockerfiles you may be working with. If it doesn't work for you, please file an issue.

## Generating a locked Dockerfile<a name="dockerfile-lock">
Because of the way Docker builds containers, Dockerfiles are generally not declarative or reflective of what ultimately gets included in the container image that gets produced. Pinning information in your Dockerfile (base OS, packages, etc.) can help create more reproducible container images should your Dockerfile be distributed to other parties. If you have a Dockerfile that you would like to lock to a more reproducible version, Tern can help.
```
$ tern lock Dockerfile
```
The locked Dockerfile will be created in `Dockerfile.lock` unless an output file is otherwise specified. To specify an output file
```
$ tern lock Dockerfile -o output.txt
```
If the packages are not pinned in the resulting `Dockerfile.lock` or output file that gets produced, it is because 1) Tern does not know the version of the packages to pin (i.e. unable to get this information from the package manager) or 2) your Dockerfile failed to build. In the case of a failed Dockerfile build, Tern only builds the base image and tries to pin what it can. If you encounter any errors, please file an issue.

# Report Formats<a name="report-formats">
Tern creates BoM reports suitable to read over or to provide to another tool for consumption.

## Human Readable Format<a name="report-human-readable">
The default report Tern produces is a human readable report. The object of this report is to give the container developer a deeper understanding of what is installed in a container image during development. This allows a developer to glean basic information about the container such as what the true base operating system is, what the app dependencies are, if the container is using an official or personal repository for sources or binaries, whether the dependencies are at the correct versions, etc.
```
$ tern report -i golang:1.12-alpine -o output.txt
```

## JSON Format<a name="report-json">
You can get the results in a JSON file to pass around in a network.
```
$ tern report -f json -i golang:1.12-alpine
```

## HTML Format<a name="report-html">
You can get an html rendering of the JSON results. An output file with `.html` suffix should be provided in order to properly view the report in your browser.
```
$ tern report -f html -i golang:1.12-alpine -o report.html
```

## YAML Format<a name="report-yaml">
You can get the results in a YAML file to be consumed by a downstream tool or script.
```
$ tern report -f yaml -i golang:1.12-alpine -o output.yaml
```

## SPDX tag-value Format<a name="report-spdxtagvalue">
[SPDX](https://spdx.org/) is a format developed by the Linux Foundation to provide a standard way of reporting license information. Many compliance tools are compatible with SPDX. Tern follows the [SPDX specifications](https://spdx.org/specifications) specifically the tag-value format which is the most compatible format with the toolkit the organization provides. The tag-value format is the only SPDX format Tern supports. There are conversion tools available [here](https://github.com/spdx/tools) (some still in development). You can read an overview of the SPDX tag-value specification [here](./docs/spdx-tag-value-overview) and about how Tern maps its properties to the keys mandated by the spec [here](./docs/spdx-tag-value-mapping.md).
```
$ tern report -f spdxtagvalue -i golang:1.12-alpine -o spdx.txt
```

# Extensions<a name="extensions">
Tern does not have its own file level license scanner. In order to fill in the gap, Tern allows you to extend container image analysis with an external file analysis CLI tool or Python3 module. In order to take advantage of the extensions, both the extention tool and Tern need to be installed.

NOTE: Neither the Docker container nor the Vagrant image has any of the extensions installed. You are welcomed to modify `Dockerfile` and `vagrant/bootstrap.sh` to install the extensions if you wish to use them. Please see the instructions below on how to enable the extension of your choice.

## Scancode<a name="scancode">
[scancode-toolkit](https://github.com/nexB/scancode-toolkit) is a license analysis tool that "detects licenses, copyrights, package manifests and direct dependencies and more both in source code and binary files". Note that Scancode currently works on Python 3.5 and 3.6 but not 3.7 onwards. Be sure to check what python version you are using below.

1. Install system dependencies for Scancode (refer to the [Scancode GitHub repo](https://github.com/nexB/scancode-toolkit) for instructions)

2. Setup a python virtual environment
```
$ python3 -m venv scanenv
$ cd scanenv
$ source bin/activate
```
3. Install tern and scancode
```
$ pip install tern scancode-toolkit
```
4. Run tern with scancode
```
$ tern report -x scancode -i golang:1.12-alpine
```

If you are running Scancode for the first time, depending on the size of the container image, it takes anywhere between 10 minutes to a few hours to run due to the number of files needed to be analyzed. Once completed, subsequent runs will be much faster as the data will be cached for future use.

## cve-bin-tool<a name="cve-bin-tool">
[cve-bin-tool](https://github.com/intel/cve-bin-tool) is a command line tool which "scans for a number of common, vulnerable components (openssl, libpng, libxml2, expat and a few others) to let you know if your system includes common libraries with known vulnerabilities". Vulnerability scanning tools can also be extended to work on containers using Tern, although support for certain metadata pertaining to CVEs may not be available yet. As a result, you will not see any of the results in the generated reports.

1. Install system dependencies for cve-bin-tool (refer to the [cve-bin-tool GitHub repo](https://github.com/intel/cve-bin-tool) for instructions)

2. Setup a python virtual environment
```
$ python3 -m venv scanenv
$ cd scanenv
$ source bin/activate
```
3. Install tern and cve-bin-tool
```
$ pip install tern cve-bin-tool
```
4. Run tern with cve-bin-tool
```
$ tern report -x cve_bin_tool -i golang:1.12-alpine
```
 
# Running tests<a name="running-tests">
WARNING: The `test_util_*` tests are not up to date. We are working on it :). From the Tern repository root directory run:
```
$ python tests/<test file>.py
```

## Project Status<a name="project-status"/>
Release 2.2.0 is out! See the [release notes](docs/releases/v2_2_0.md) for more information.

We try to keep the [project roadmap](./docs/project-roadmap.md) as up to date as possible. We are currently working on Release 3.0.0.

## Releases
* [v2.2.0](docs/releases/v2_2_0.md)
* [v2.1.0](docs/releases/v2_1_0.md)
* [v2.0.0](docs/releases/v2_0_0.md)
* [v1.0.1](docs/releases/v1_0_1.md)
* [v0.5.4](docs/releases/v0_5_4.md)
* [v0.4.0](docs/releases/v0_4_0.md)
* [v0.3.0](docs/releases/v0_3_0.md)
* [v0.2.0](docs/releases/v0_2_0.md)
* [v0.1.0](docs/releases/v0_1_0.md)

## Documentation
Architecture, function blocks, code descriptions and the project roadmap are located in the docs folder. Contributions to the documentation are welcome! See the [contributing guide](/CONTRIBUTING.md) to find out how to submit changes.

## Get Involved

Do you have questions about Tern? Do you think it can do better? Would you like to make it better? You can get involved by giving your feedback and contributing to the code, documentation and conversation!

Please read our [code of conduct](/CODE_OF_CONDUCT.md) first.

Next, take a look at the [contributing guide](/CONTRIBUTING.md) to find out how you can start.
