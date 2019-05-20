# Project Road Map

## 2019

Since 2018, Tern has [joined the Linux Foundation](https://www.linuxfoundation.org/press-release/2018/12/the-linux-foundation-to-launch-new-tooling-project-to-improve-open-source-compliance/). As a result, many of the project's goals will be aligned with the goals of the ACT project. This basically means some more resources will go towards making the project easier for developers to use while *gently* motivating them to follow some best practices. With that in mind, we will be focusing on the [SPDX superbug](https://github.com/vmware/tern/issues/174) for release 0.4.0 slated for May of 2019.

CI/CD for the project has now become a priority. We can't sustain further community growth without it. So for release 0.5.0 slated for August of 2019, we will focus on these items:

- Setting up Circle CI to run linting with Prospector
- Setting up a Build and Release pipeline where PyPI package managers and Dockerhub container images can be distributed
- Setting up Circle CI to run tests based on files touched

This might turn into a small release as I am on vacation for most of the month of July. However I will do some backlog scrubbing and some of these items might be included:

- Using the [stevedore](https://github.com/openstack/stevedore) module to dynamically load templates.
- Some refactoring to lay the groundwork for enabling language level package managers.

We will then be ready to focus on enabling our first language level package manager - pip. We also have a bunch of technical debt to tackle. So we will focus on these for release 0.6.0 slated for November of 2019.

This timetable is based on time, resources and feedback from you and will change accordingly.

See archived roadmaps [here](project-roadmap-archive.md)
