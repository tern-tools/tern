# Navigating Tern's Code

To help with code navigation, looking up the [glossary](/docs/glossary.md) is useful

Here is a layout of the directory structure:

```
|--- classes
|    |--- package.py (Package class)
|    |--- image_layer.py (ImageLayer class)
|    |--- image.py (abstract Image class)
|    |--- docker_image.py (DockerImage class)
|    |--- command.py (Command class)
|    |--- notice.py (Notice class)
|    |--- notice_origin.py (NoticeOrigin class)
|    └--- origins.py (Origins class)
|
|--- command_lib
|    |--- command_lib.py (operations on the command library)
|    |--- base.yml (command library for base images)
|    └--- snippets.yml (command library for code snippets)
|
|--- docs (where all the documentation lives)
|
|--- report
|    |--- content.py (content generation)
|    |--- errors.py (error messages)
|    |--- formats.py (report formats or string snippets)
|    └--- report.py (report collation operations)
|
|--- samples (sample Dockerfiles)
|
|--- scripts (where container or host runnable scripts live)
|
|--- tests (unit and functional tests)
|
|--- utils
|    |--- cache.py (cache operations)
|    |--- constants.py (constants)
|    |--- container.py (container operations - currently docker related)
|    |--- dockerfile.py (dockerfile parser)
|    |--- general.py (general operations)
|    └--- metadata.py (container image metadata operations)
|
|--- cache.yml (container layer cache)
|
|--- common.py (common subroutines)
|
|--- docker.py (docker related subroutines)
|
└--- tern (the main executable)
```

Some general rules about where the code is located:
- Utilities used anywhere in the project go in utils
- Class definitions go in classes. For clarity, the name of the file is also the name of the class but with an underscore separating the words rather than CamelCase
- Any operation related to look up and operations with the Command Library go in command_lib
- Any documentation goes in docs.
- Any operations related to reporting go in report.
- Any sample Dockerfiles go in samples. The directory structure needs to be such that the Dockerfile exists along with the image context. This means that when you use "docker build" only the Dockerfile gets sent to the docker daemon rather than the whole directory structure. This saves on build time.
- The scripts directory is not used by the project yet, but there is potential to use it for complicated operations such as extracting source tarballs
- All unit and functional tests go in tests

Code organization follows these general rules:
- Each class is in its own file
- Utils are organized based on what they operate on
- Subroutines that require the use of modules from all over the project live in high level files like common.py and docker.py 
