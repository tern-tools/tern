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


### TODO
- Move the pieces to extract sources for packages and versions from here
- Make a module called report.py to handle reporting functions
- Add a module to dockerfile.py to make subsections of docker instructions to handle multistage docker builds
- Accept arguments for --build-args
- Update this README
