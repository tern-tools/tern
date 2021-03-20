# Project Road Map

## 2021
We are getting very close to a beta release. Our beta release is targeted for the summer timeframe.

Our goal is to meet these requirements by the end of the year.
- We are working towards enabling "live" analysis for a container. The idea is that if Tern could generate an SBoM at build time, the SBoM would then be available to package and distribute with the container image without the need for post scanning.
- We are very close to enabling inventory for a single container layer which will be available in the next 2.5.0 release.
- We will continue investigating how we can run Tern without root privileges.
- We want to enable Tern to pull image digests and images using registry HTTP(s) APIs so that we can pull images from registries other than Dockerhub.
- Create a database backend with an associated API. We are hoping to have a GSoC intern help us tackle this issue.
- Enable inventory of a Distroless image using some sort of custom script.


We will also continue to work on the following:
- We will continue to support the SPDX format for container images. To that end, we will make changes to update the format of the document as the [spec](https://spdx.org/sites/cpstandard/files/pages/files/spdxversion2.1.pdf) evolves.
- As usual, we will continue to work on our technical debt and bug fixes.

This timetable is based on time, resources and feedback from you and will change accordingly.

See archived roadmaps [here](project-roadmap-archive.md)

[Back to the README](../README.md)
