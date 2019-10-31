# Glossary of Terms

- Command Library: Tern references a database of shell commands to determine what packages got installed. This is called the "Command Library".
- Report: the artifact produced after running Tern. This is either a text document or a machine readable format.
- Image: A container image, typically created by [Docker](https://www.docker.com/) or following the [OCI image specification](https://github.com/opencontainers/image-spec/blob/master/spec.md)
- Layer: A root filesystem or the difference between a previous filesystem and a new filesystem as created by storage drivers like AUFS or OverlayFS. See the [OCI Image Layer specification](https://github.com/opencontainers/image-spec/blob/master/layer.md) for a general overview of how layer filesystems are created.
- Package: A software package or library
- Notice: A record of an incident that Tern came across during execution
- Notice Origin: The location from which the Notice came. This can be the container or Dockerfile or Command Library or something in the development environment.
- Cache: A database that associates container layer filesystems with the packages that were installed on them. Currently this is only represented by a yaml file and some CRUD operations against it.
- Dockerfile: A file containing instructions to the [Docker](https://docs.docker.com/engine/reference/commandline/build/) daemon on how to build a container image.
- Extension: An external tool Tern can use to analyze a container image

[Back to the README](../README.md)
