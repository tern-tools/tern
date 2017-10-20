### What is Tern?

Tern is a tool to find the metadata for packages installed in Docker containers, specifically the sources, versions and licenses. It does this by looking up
a "command library" for code snippets to execute in a running container. The command library is a list of shell commands used to install and remove packages
with associated shell commands to run within the container to retrieve specific information.

Tern was created to address the issue that Docker containers where distributed without certainity of what packages they contained. This becomes especially problematic when distributing packages with incompatible licenses or licenses that have restrictions on distribution.

### Requirements
- Git (Installation instructions can be found here: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Docker CE (Installation instructions can be found here: https://docs.docker.com/engine/installation/#server)
- Python 3.6.2 (sudo apt-get install python3.6 or sudo dnf install python36)

### Getting Started
Once you have installed the requirements you can run these commands in a terminal to get you started:
```
$ python3 -m venv ternenv
$ cd ternenv
$ git clone git@gitlab.eng.vmware.com:opensource/tern.git
$ source bin/activate
$ cd tern
$ pip install -r requirements.txt
$ ./tern report -d samples/debian_vim/Dockerfile
```
If you come across any issues, please file a bug with the complete output. If it completes successfully, take a look at report.txt. You can file bugs against the report as well

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
