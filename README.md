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
