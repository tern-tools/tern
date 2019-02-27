# Project Road Map

## 2019

Since 2018, Tern has [joined the Linux Foundation](https://www.linuxfoundation.org/press-release/2018/12/the-linux-foundation-to-launch-new-tooling-project-to-improve-open-source-compliance/). As a result, many of the project's goals will be aligned with the goals of the ACT project. This basically means some more resources will go towards making the project easier for developers to use while *gently* motivating them to follow some best practices. With that in mind, we will be focusing on the [SPDX superbug](https://github.com/vmware/tern/issues/174) for release 0.4.0 slated for May of 2019.

We will then be ready to focus on enabling our first language level package manager - pip. This enabling will include:
- Creating scripts to add to the command library in base.yml
- Updating verify_invoke.py to empower users to test their script additions
- Update the documentation for enabling a package manager

We will focus on these for release 0.5.0 slated for August of 2019.

We will then shift to enabling some CI/CD and build and release pipelines for the releases. This will include:
- Setting up Circle CI to make conditional testing based on files that were changed.
- Fix the unit tests for the classes
- Make a Dockerhub and PyPI release
- Document our build and release process

We will focus on these for release 0.6.0 slated for November of 2019

This timetable is based on time, resources and feedback from you and will change accordingly.

See archived roadmaps [here](project-roadmap-archive.md)
