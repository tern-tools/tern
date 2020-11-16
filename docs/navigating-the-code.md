# Navigating Tern's Code

To help with code navigation, looking up the [glossary](/docs/glossary.md) is useful. All the code lives in the directory `tern`. The rest of the files in the root repository have to do with configurations for build and packaging. If you want to try each of the modules in the Python repl (Read Eval Print Loop), you can reference them from the module `tern`. For example:

```
from tern.utils import rootfs
from tern.analyze.default import core
```

Here is a layout of the directory structure:

```
▾ tern/
    __main__.py 	  <-- tern entry point (where command line argument parsing lives)
    prep.py 		  <-- set-up and tear-down operations
  ▾ analyze/
      common.py 	  <-- common functions for analysis
      passthrough.py 	  <-- functions to hand off analysis to an extension
    ▾ default/ 		  <-- tern's default analysis method
        bundle.py	  <-- functions to bundle collected data into an Image class
        collect.py	  <-- functions to collect data
        core.py		  <-- core subroutines for tern's default operation
        default_common.py <-- common functions for default operation
        filter.py
      ▸ command_lib/      <-- tern's command library
      ▸ container/	  <-- functions to analyze a container image
      ▸ dockerfile/	  <-- functions to analyze/lock a Dockerfile
  ▾ classes/		  <-- python classes to store data collected during analysis
      command.py
      docker_image.py
      file_data.py
      image.py
      image_layer.py
      notice.py
      notice_origin.py
      origins.py
      package.py
      template.py
  ▾ extensions/		  <-- supported extensions
    ▸ cve_bin_tool/
    ▸ scancode/
      executor.py
  ▾ formats/		  <-- supported reporting formats
    ▸ default/
    ▸ html/
    ▸ json/
    ▸ spdx/
    ▸ yaml/
      generator.py
  ▾ load/		  <-- functions to fetch and extract container images
      docker_api.py
  ▾ report/		  <-- functions for printing strings in the report
      content.py
      errors.py
      formats.py
      report.py
  ▸ scripts/		  <-- external scripts
  ▸ utils/		  <-- utilities that are used throughout the code

```

Tests live outside of the `tern` folder, in a folder called `tests`. The file name format is typically `test_path_to_python_file.py` with the exception of `test_fixtures.py` which are classes used for testing 

```
▾ tests/                                                                                                                                                                                                                        
    test_analyze_common.py
    test_analyze_default_common.py
    test_analyze_default_dockerfile_parse.py
    test_analyze_default_filter.py
    test_class_command.py
    test_class_docker_image.py
    test_class_file_data.py
    test_class_image.py
    test_class_image_layer.py
    test_class_notice.py
    test_class_notice_origin.py
    test_class_origins.py
    test_class_package.py
    test_class_template.py
    test_fixtures.py				<-- classes for testing purposes live here
    test_load_docker_api.py
    test_util_general.py
  ▸ dockerfiles/				<-- Test dockerfiles live here

```

Scripts used by our CI/CD setup live outside the `tern` folder, in a folder called `ci`.

```
▾ ci/
    Dockerfile 	           <-- Dockerfile used to test the tip of default branch in a docker container
    evaluate_docs.py
    test_commit_message.py
    test_files_touched.py
```

Documentation lives in a folder called `docs`. Sample Dockerfile live in a folder called `samples`.

Some general rules about where the code is located:
- Utilities used anywhere in the project go in `tern/utils`.
- Class definitions go in `tern/classes`. For clarity, the name of the file is also the name of the class but with an underscore separating the words rather than CamelCase.
- Any operation that is performed by default (when running `tern report -i image:tag` live in `tern/analyze/default` as opposed to running tern with an extension (`tern report -x scancode -i image:tag`.
- Any operation related to look up and operations with the Command Library go in `tern/analyze/default/command_lib`.
- Any documentation goes in `docs`.
- Any operations related to string manipulation go in `tern/report`.
- Any sample Dockerfiles go in `samples`. The directory structure needs to be such that the Dockerfile exists along with the image context. This means that when you use "docker build" only the Dockerfile gets sent to the docker daemon rather than the whole directory structure. This saves on build time.
- The `scripts` directory is not used by the project yet, but there is potential to use it for complicated operations such as extracting source tarballs.
- All unit and functional tests go in `tests`.

Code organization follows these general rules:
- Each class is in its own file.
- Utils are organized based on what they operate on.
- Subroutines usually live in a file named for a particular high-level operation. Please refer to the layout of the code to get an idea of what operation corresponds to what file.

As a community, we try to make it as easy as possible for the code to be approachable. As such, we try to minimize the complexity of the code by following these guidelines:
- Write simple functions whenever possible. If you find you are using more than 5 arguments or more than 3 if and for loops, try to make a new function that could be called within the original function.
- Minimize the number of lines in a file. Maintaining large files can be overwhelming. It's totally fine to created a new file if the existing file that is being edited becomes too large.
- Provide adequate documentation for each of the functions. Describing what the inputs, outputs and operations are for a function will go a long way for others in the community to understand the function operation.
- Create functions and files in the appropriate place in the codebase. If you are unsure where to create new functions or files, just ask in the GitHub issue you are working on, or create a new one.

[Back to the README](../README.md)
