### Requirements
- Python 3.5

### Usage
```
$ pyvenv testenv
$ cd testenv
$ git clone ssh://git@git.eng.vmware.com/ostc/docker-compliance.git
$ source bin/activate
$ cd docker-compliance
$ pip install -r requirements.txt
$ python demo.py '/path/to/dockerfile'
```

### To run a test
```
$ cd testenv
$ source bin/activate
$ git clone ssh://git@git.eng.vmware.com/ostc/docker-compliance.git
$ cd docker-compliance
$ export PYTHONPATH=`pwd`
$ python tests/<test file>.py
```

### TODO

#### Phase 2:

1. Knowledge base: Each layer hash should come with a list of known packages that are installed in that layer
2. Allow for exceptions or additions for the command library
3. In the reporting do not ignore packages that may be installed in the docker image - see bug 4
4. Harden for testing within VMware's docker community

### Bugs:
1. Script assumes user is not in the docker group
2. When a command fails within a container that package should be moved over to 'unrecognized'
3. For reporting purposes - parse ENV
4. Report should have 3 sections: confirmed, unconfirmed, unrecognized
5. docker-command should raise exceptions that can be caught in demo for exiting

### Upstream potential:
1. Docker API assumes user is in docker group and hence can run docker commands without sudo
2. Docker has no ability to step through docker history
