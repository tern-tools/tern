# FAQ (Work in Progress)

## Why Tern?
Tern was created to help developers meet open source compliance requirements for containers. Open source software compliance is a hard problem in general but it gets harder with containers due to the ability to reuse diff filesystems. How those filesystems were created is still an ad hoc process. If you happen to have a LWN subscription you can read an article about it [here](https://lwn.net/Articles/752982/).

The first step in meeting open source compliance obligations is knowing your container's Bill of Materials or BoM. This knowledge gives you some added benefits like debugging integration and build errors and identifying vulnerable packages in your running containers.

## Why not filesystem scanning?
Static analysis is a reasonable approach to find software components and there are tools like [clair](https://github.com/coreos/clair) that create a BoM as part of vulnerability scanning. Some things to consider when using static analysis are the number of false positives that are detected, the time it takes to scan numerous files (some of which may not even be needed for an application to work) and the reliance on data that may not be open sourced. Tern is not meant to be a replacement for static analysis but simply a tool that automates some of the methods that developers and sysadmins use anyway.

## Why Python?
Python is well suited for easy string formatting which is most of the work that Tern does.

[Back to the README](../README.md)
