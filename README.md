![Tern](/docs/img/tern_logo.png)

[![Build Status](https://travis-ci.com/vmware/tern.svg?branch=master)](https://travis-ci.com/vmware/tern)

# Welcome to the Tern Project

Tern is a software package inspection tool for containers. It's written in Python3 with a smattering of shell scripts.

## Quick Links
- [Quick Start](#getting-started)
- [Start Contributing](CONTRIBUTING.md)

## What is Tern?
Tern is an inspection tool to find the metadata of the packages installed in a container image. The overall operation looks like this:
1. It uses overlayfs to mount the first filesystem layer in a container image
2. It then executes scripts from the "command library" in a chroot environment to collect information about packages installed in that layer
3. With that information as a base, it continues to iterate over steps 1 and 2 for the rest of the layers in the container image
4. Once done, it generates a report in different formats. The default report is a verbose explanation of what layers brought in what software components. If a Dockerfile is provided then it will also provide what lines in the Dockerfile was used to create the layers.

Tern gives you a deeper understanding of your container's bill of materials so you can make better decisions about your container based infrastructure, integration and deployment strategies. It's also a good tool if you are curious about the contents of the container images you have built.

![Tern quick demo](/docs/img/tern_demo_fast.gif)

## Table of Contents
- [FAQ](/docs/faq.md)
- [Getting Started](#getting-started)
- [Project Status](#project-status)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Glossary of Terms](/docs/glossary.md)
- [Architecture](/docs/architecture.md)
- [Navigating the Code](/docs/navigating-the-code.md)

## Getting Started<a name="getting-started"/>

### Getting Started with Docker
Docker is the most widely used tool to build and run containers. If you already have Docker installed, you can run Tern by building a container with the Dockerfile provided and the `docker_run.sh` script:

```
$ git clone https://github.com/vmware/tern.git
$ docker build -t ternd .
$ ./docker_run workdir ternd "report -i debian:buster" > output.txt
```

To produce a json report run
```
$ ./docker_run workdir ternd "report -j -i debian:buster"
```

What the `docker_run.sh` script does is create the directory `workdir` if not present in your current working directory and run the built container as privileged with `workdir` bind mounted to it.

*WARNING:* privileged Docker containers are not secure. DO NOT run this container in production unless you have secured the node (VM or bare metal machine) that the docker daemon is running on.

### Getting Started with Vagrant
Vagrant is a tool to setup an isolated virtual software development environment. Follow [these steps](/docs/contributing-setup.md) to set up your Vagrant environment. This is a requirement if you are using Windows or Mac OSs.


### Getting Started on Linux
If you have a Linux OS you will need a distro with a kernel version >= 4.0 (Ubuntu 16.04 or newer or Fedora 25 or newer are good selections) and will need to install the following requirements:

- Git (Installation instructions can be found here: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- attr (sudo apt-get install attr or sudo dnf install attr)
- Python 3.6 or newer (sudo apt-get install python3.6(3.7) or sudo dnf install python36(37))

If you happen to be using Docker containers
- Docker CE (Installation instructions can be found here: https://docs.docker.com/engine/installation/#server)

Make sure the docker daemon is running.

*NOTE:* Tern currently supports containers built with Docker but it is architected to support other container image formats.

Create a python3 virtual environment and install requirements

```
$ python3 -m venv ternenv
$ cd ternenv
$ git clone https://github.com/vmware/tern.git
$ source bin/activate
$ cd tern
$ git checkout -b release v0.3.0 <-- optional stable placeholder
$ pip install -r requirements.txt
$ cd src
$ ./tern -l report -f output.txt -i debian:buster
```

### To run against a Docker image
If you have a Docker image pulled locally and want to inspect it
```
$ ./src/tern report -i debian:jessie
```
Take a look at report.txt to see what packages are installed in the Docker image and how Tern got this information. If you encounter any errors, please file an issue.

### To run against a Dockerfile
You can run Tern against a Dockerfile. Tern will build the image for you and then analyze it with respect to the Dockerfile
```
$ cd src
$ ./tern report -d samples/photon_git/Dockerfile
```
Take a look at report.txt to see what packages are installed in the created Docker image and how Tern got this information. Feel free to try this out on the other sample Dockerfiles in the samples directory or on Dockerfiles you may be working with. If it doesn't work for you, please file an issue.

### To get a summary report
To get just a list of packages, you can use the `-s` option to get a summary report.
```
$ cd src
$ ./tern report -s -d samples/photon_git/Dockerfile
```
WARNING: Tern is meant to give guidance on what may be installed in a container image, so it is recommended that for the purpose of investigation, the default report is used. The summary report may be used as the output of a build artifact or something to submit to a compliance or legal team.

### To get the results in YAML form
To get the results in a YAML file to be consumed by a downstream tool or script
```
$ cd src
$ ./tern report -y -i debian:jessie
```

### To get the results in JSON form
To get the results in a JSON file for web use
```
$ cd src
$ ./tern report -j -i debian:jessie
```

### To run a test
```
$ cd ternenv
$ source bin/activate
$ git clone https://github.com/vmware/tern.git
$ cd tern
$ export PYTHONPATH=`pwd`/src
$ python tests/<test file>.py
```

## Project Status<a name="project-status"/>
Release 0.3.0 is here! Some items for the release have been moved back to the backlog.

- I am moving the [PyPI package issue](https://github.com/vmware/tern/issues/136) to the near future backlog. I would like to have a build and release pipeline set before implementing this. This is the same reason why I haven't pushed any Docker images to Dockerhub yet and have rather defaulted to folks building the container themselves.
- I've moved the [install script issue](https://github.com/vmware/tern/issues/21) to the far future backlog. We may not even implement this if the pip package and docker containers are in place. Install scripts are notoriously hard to maintain.
- I'll be closing all Travis CI issues due to the [news](https://twitter.com/ReinH/status/1098663375985229825). I'll be reopening the same issues with Circle CI. Expect the travis.yml to go away soon. This makes me feel angry-sad, but for the sake of the project's health, I think this is a reasonable decision to make.

We try to keep the [project roadmap](./docs/project-roadmap.md) as up to date as possible. We are currently working on Release 0.4.0

## Releases
* [v0.1.0](docs/releases/v0_1_0.md)
* [v0.2.0](docs/releases/v0_2_0.md)
* [v0.3.0](docs/releases/v0_3_0.md)

## Documentation<a name="documentation"/>
Architecture, function blocks, code descriptions and the project roadmap are located in the docs folder. Contributions to the documentation are welcome! See the [contributing guide](/CONTRIBUTING.md) to find out how to submit changes.

## Get Involved<a name="contributing"/>

Do you have questions about Tern? Do you think it can do better? Would you like to make it better? You can get involved by giving your feedback and contributing to the code, documentation and conversation!

Please read our [code of conduct](/CODE_OF_CONDUCT.md) first.

Next, take a look at the [contributing guide](/CONTRIBUTING.md) to find out how you can start.
