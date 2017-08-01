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
#### Immediate:
1. Update this README with a problem statement and high level design
2. Clean up reporting
3. Add back the retrieval bit
4. Test with a variety of docker images and file the bugs here
#### Later:
- Add a module to dockerfile.py to make subsections of docker instructions to handle multistage docker builds
- Accept arguments for --build-args

### Bugs:
1. Script assumes user is not in the docker group
2. When a command fails within a container that package should be moved over to 'unrecognized'
3. For reporting purposes - parse ENV
4. Report should have 3 sections: confirmed, unconfirmed, unrecognized
5. Add ability to parse image tarfiles
