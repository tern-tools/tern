![Tern](/docs/img/tern_logo.png)

### Welcome to the Tern Project

Tern is a tool to find the metadata for packages installed in Docker containers, specifically the sources, versions and licenses. It does this by looking up
a "command library" for code snippets to execute in a running container. The command library is a list of commands used to install and remove packages
(such as a package manager) with associated shell commands to run within the container to retrieve specific information.

Tern was created to help developers meet open source compliance requirements for containers. Tools like Docker make it easy to build and distribute containers but keeping track of what is installed is left to developer or devops teams. Tern aims to bridge this gap.

### Try it out

#### Requirements
- Git (Installation instructions can be found here: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Docker CE (Installation instructions can be found here: https://docs.docker.com/engine/installation/#server)
- Python 3.6.2 (sudo apt-get install python3.6 or sudo dnf install python36)

Make sure the docker daemon is running. If it is you can run these commands to get you started:
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

#### To get a summary report
```
$ ./tern report -s -d samples/photon_git_Dockerfile
```
WARNING: Tern is meant to give guidance on what may be installed for each line in a Dockerfile so it is recommended that for the purpose of investigation, the default report is used. The summary report may be used as the output of a build artifact or something to submit to a compliance or legal team.

#### To run a test
```
$ cd ternenv
$ source bin/activate
$ git clone https://github.com/vmware/tern.git
$ cd tern
$ export PYTHONPATH=`pwd`
$ python tests/<test file>.py
```
### Project Status

Tern currently has these features:
* A Cache to store layers with the packages that are installed in those layers
* A report containing a line-by-line 'walkthrough' of the Dockerfile to say what packages were installed in each line
* A summary report
* The complete list of dependencies are retrieved

Current work:
* Code refactoring
* Layering of container filesystems one by one
* Source retrieval

### Documentation
Architecture, function blocks, code descriptions and the project roadmap are located on the Wiki. Feel free to use it as a guide to usage and development. We also welcome contributions to the documentation. See the [contributing guide](/CONTRIBUTING.md) to find out how to submit changes.

### Get Involved

Do you have questions about Tern? Do you think it can do better? Would you like to make it better? You can get involved by giving your feedback and contributing to the code, documentation and conversation!

Please read our [code of conduct](/CODE_OF_CONDUCT.md) first.

Next, take a look at the [contributing guide](/CONTRIBUTING.md) to find out how you can start.
