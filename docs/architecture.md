# Tern Architecture

You may want to look at the [glossary](./glossary.md) to understand the terms being used.

## Overall Approach
The general approach to finding package metadata given some files is to perform static analysis on the files. Tern's approach is more brute force - using the same tools that were used to install a package to retrieve the status of the package. This involves spinning up a container and running shell commands against it. The results of the shell commands are then collated into a nice report showing which container layers brought in what packages. For compliance purposes (as Tern is a compliance tool), shell scripts retrieving package versions, licenses and source urls are used. Tern is also built to be a tool for guidance, and to that effect it is opinionated. For example, if it cannot find information about licenses, it will inform you of this and nudge you to either add information about it or a shell script to retrieve it.

## Guiding Principles
1. OSS Compliance First: Tern is a compliance tool at heart. Hence whatever it does is meant to help the user meet their open source compliance obligations, or, at the minimum, make them aware of the licenses governing the open source software they use.
2. Be Transparent: Tern will report on everything it is doing in order to not mislead on how it got its information
3. Inform not Ignore: Tern will report on all exceptions it has encountered during the course of its execution

## Layout
There are 3 sections that operate together:

### The Cache
This is the database where filesystem identifiers can be queried against to retrieve package information. This is useful as many containers are based on other container images. If Tern had come across the same filesystem in another container, it can retrieve the package information without spinning up a container. Tern looks for filesystems here before spinning up a container for analysis.

### The Command Library
This is a database of shell commands that may be used to create a container's layer filesystem. There are two types of shell commands - one for base images and one for standalone shell commands. The library is split in this way to account for situations where whole root filesystems are imported in order to create a new container.

For example, in [this Dockerfile sample](../samples/debian_vim/Dockerfile), the use of FROM debian:jessie imports the base debian:jessie image from Dockerhub. This image is in turn created with a [Dockerfile](https://github.com/debuerreotype/docker-debian-artifacts/blob/b024a792c752a5c6ccc422152ab0fd7197ae8860/jessie/Dockerfile) that has the FROM scratch directive and adds an entire root filesystem created from an external build an release pipeline not related to Docker. The base library is meant to keep track of such images. On the other hand, the snippets library is used to keep track of standalone shell commands that can be used to install packages, once you hava a base image to work on.

Some acknowledgement should be made here that this is not the only way to create a container. However, it seems to be the most prevalent way and a way that makes sense to most people creating containers and tools like Docker allow for this to be done easily.

### The Reporting
Tern's main purpose is to produce reports, either as an aid for understanding a container image or as a manifest for something else to consume. The default is the verbose report explaining where in the container the list of packages came from and what commands created them. The easiest format to consume is actually cache.yml that only contains the filesystem layer identifier and the list of packages installed in it. Support for other types of formats are available using format converters. A summary text format is also available containing just the packages installed.

## Process Flow
The flowchart here shows the general flow of control
![Tern process flow](/img/tern_flow.png)

## Objects
Tern uses classes to encapsulate some of the objects that it will be referencing during thr course of execution. They can be found in the classes directory. The general format is that Image contains a list of type ImageLayer and each ImageLayer contains a list of type Package. On top of that each of those objects contain an object of type Origins. The Origins object contains a list of type NoticeOrigin which contains a list of type Notice.

A Notice object is where notice messages and the notice levels are recorded. Right now there are 4 notice levels: 'error', 'warning', 'hint' and 'info'. The 'hint' is not so much as to indicate the gravity of the notice but to inform the user on the best way to remove the notice.

## Utilities
The utility modules are organized in files under specific operations in the utils folder. They are used across the whole project. They should be operational by themselves and can be used independent of the main tern executable. For example, cache.py can implement cache CRUD operations that could be used through some API as well as the executable. Typically, utilities raise errors that other modules may implement in a try-catch. So they can be considered as low-level modules.

## Subroutines
The subroutines that run some common steps that could be used anywhere in the project are located in common.py. There is also a dockery.py file that contains subroutines specific to Docker containers. There is room for these to move around as the project grows.

Check out [how to navigate the code](./navigating-the-code.md) if you are ready to contribute.
