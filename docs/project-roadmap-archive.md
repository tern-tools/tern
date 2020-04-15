## 2020-04-15
### 2019

Since 2018, Tern has [joined the Linux Foundation](https://www.linuxfoundation.org/press-release/2018/12/the-linux-foundation-to-launch-new-tooling-project-to-improve-open-source-compliance/). As a result, many of the project's goals will be aligned with the goals of the ACT project. This basically means some more resources will go towards making the project easier for developers to use while *gently* motivating them to follow some best practices. We will also be focusing on allowing Tern to better integrate with these and other projects.

For Release 0.4.0 dated May 2019, we will be focusing on the [SPDX superbug](https://github.com/vmware/tern/issues/174).

CI/CD for the project became a priority. We can't sustain further community growth without it. So for release 0.5.4 dated August 2019, we focused on these items:

- Setting up Circle CI to run linting with Prospector
- Setting up a Build and Release pipeline where PyPI package managers
- Setting up Circle CI to run tests based on files touched

This was a relatively small release as one of the maintainers was on vacation in July.

For Release 1.0.0 slated for November of 2019, we will focus on the following:

- Using the [stevedore](https://github.com/openstack/stevedore) module to dynamically load reporting formats.
- Some refactoring to allow external tools to be integrated into Tern.
- Some refactoring to allow containers built using other tools. This includes enabling Tern to use a raw container image tarball.
- Some refactoring to allow language level package managers. We will focus on pip
- Bug fixes and technical debt.


## 2019-02-27
### 2018
The end goal for 2018 is to make the project relevant to real world containers and to make it easy to contribute to it. Milestones for the project can be discussed on the community slack channel or the public forum. See the [contributing guide](../CONTRIBUTING.md) for information on how to join the conversation.

### Release 0.1.0
- Create isolated environments to operate on without using other dependencies
- Analyze a container image layer by layer
- Optimize shell script workload for package managers

### Release 0.2.0
- Work on raw container images along with Dockerfiles
- Ability to track true base images (FROM scratch in Dockerfiles)
- Support for images created from multiple imports
- Support for ADD, COPY and WORKDIR

### Release 0.3.0
- Hardening with a variety of Dockerfiles
- Support for multistage build Dockerfiles
