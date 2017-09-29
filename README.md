### What is Tern?

Tern is a tool to find the metadata for packages installed in Docker containers, specifically the sources, versions and licenses. It does this by looking up
a "command library" for code snippets to execute in a running container. The command library is a list of shell commands used to install and remove packages
with associated shell commands to run within the container to retrieve specific information.

Tern was created to address the issue that Docker containers where distributed without certainity of what packages they contained. This becomes especially problematic when distributing packages with incompatible licenses or licenses that have restrictions on distribution.

### Requirements
- Python 3.6.2 (Sorry: At this time, backwards compatibilty with Python 2.7 is not supported)

### Usage
```
$ python3 -m venv ternenv
$ cd ternenv
$ git clone git@gitlab.eng.vmware.com:opensource/tern.git
$ source bin/activate
$ cd tern
$ pip install -r requirements.txt
$ ./tern -h
```

### To run a test
```
$ cd ternenv
$ source bin/activate
$ git clone git@gitlab.eng.vmware.com:opensource/tern.git
$ cd tern
$ export PYTHONPATH=`pwd`
$ python tests/<test file>.py
```

### Milestones

#### Phase 2:

1. Knowledge base: Each layer hash should come with a list of known packages that are installed in that layer
2. Allow for exceptions or additions for the command library
3. In the reporting do not ignore packages that may be installed in the docker image
4. Harden for testing within VMware's docker community

### Bugs:
1. For reporting purposes - parse ENV
2. Keeps running docker save even if it already exists on the filesystem
3. Reporting of errors in docker commands are not recorded in the report
4. The container is shut down and brought up for every invoke
5. Too much noise in the docker command - no need to report unless there was an error

### Feature requests:
1. Logging
2. Create install script

### Upstream potential:
1. Docker API assumes user is in docker group and hence can run docker commands without sudo
2. Docker has no ability to step through docker history
